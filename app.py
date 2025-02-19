from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import db, bcrypt, User, Bank,Transaction





app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'SECRETKEY'

db.init_app(app)
bcrypt.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'





@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        mobile = request.form["mobile"]

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        new_user = User(name=name, email=email, mobile=mobile)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("profile"))

        flash("Invalid credentials!", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        
        # Check if email is being changed and if it's already taken
        if email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash("Email already in use!", "danger")
                return redirect(url_for("edit_profile"))

        # Update user information
        current_user.name = name
        current_user.email = email
        current_user.mobile = mobile

        try:
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("showbank"))
        except:
            db.session.rollback()
            flash("Error updating profile!", "danger")
            return redirect(url_for("edit_profile"))

    return render_template("edit_profile.html", user=current_user)



@app.route("/showbank")
@login_required
def showbank():
    return render_template("showbank.html", user=current_user, bank_accounts=current_user.bank_accounts)

@app.route("/addbank", methods=["GET", "POST"])
@login_required
def addbank():
    if request.method == "POST":
        bankaccount = request.form.get("bankaccount")
        name = request.form.get("name")
        ifsc = request.form.get("ifsc")
        bname = request.form.get("bname")

        new_bank = Bank(
            bankaccount=bankaccount,
            name=name,
            ifsc=ifsc,
            bname=bname,
            user_id=current_user.id
        )

        db.session.add(new_bank)
        db.session.commit()
        flash("Bank account added successfully!", "success")
        return redirect(url_for("showbank"))

    return render_template("addingbankaccount.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)




@app.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("showbank"))




@app.route('/delete_bank/<string:bank_account_number>', methods=['POST'])
def delete_bank(bank_account_number):
    bank = Bank.query.filter_by(bankaccount=bank_account_number).first()
    if bank:
        db.session.delete(bank)
        db.session.commit()
        flash("Bank account deleted successfully!", "success")
    else:
        flash("Bank account not found!", "danger")
    return redirect(url_for('showbank'))  # Adjust the redirection if needed



# finance
# Home Route
@app.route('/financetracker')
@login_required  # Ensure only logged-in users access this page
def financetracker():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('financetracker.html', transactions=transactions)


# Add Transaction
@app.route('/add', methods=['POST'])
@login_required  # 🔹 Ensures only logged-in users can add transactions
def add_transaction():
    category = request.form.get('category')
    amount = request.form.get('amount')
    description = request.form.get('description')

    if category and amount:
        new_transaction = Transaction(
            category=category, 
            amount=float(amount), 
            description=description, 
            user_id=current_user.id  # 🔹 Assign transaction to logged-in user
        )
        db.session.add(new_transaction)
        db.session.commit()
        flash("Transaction added successfully!", "success")

    return redirect(url_for('financetracker'))


# Delete Transaction
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    
    # 🔹 Ensure the user is deleting their own transaction
    if transaction.user_id != current_user.id:
        flash("Unauthorized action!", "danger")
        return redirect(url_for("financetracker"))

    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted successfully!", "success")
    return redirect(url_for('financetracker'))



# Edit Transaction Page
@app.route('/edit/<int:id>')
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    return render_template('update.html', transaction=transaction)

# Update Transaction
@app.route('/update/<int:id>', methods=['POST'])
def update_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    transaction.category = request.form.get('category')
    transaction.amount = float(request.form.get('amount'))
    transaction.description = request.form.get('description')
    
    if not transaction.category or not transaction.amount:
        return "Error: Category and amount cannot be empty.", 400

    db.session.commit()
    return redirect(url_for('financetracker'))



# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

