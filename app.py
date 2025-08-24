# Inventory Management Software for Company selling Automotive Parts

from flask import Flask, render_template, session, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecret"
# Database connection
conn = mysql.connector.connect(
    host = "127.0.0.1",
    user = "root",
    password = "password",
    database = "Cars"
)
cursor = conn.cursor(buffered=True)

#Login Page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        accepted_user_pwd = ["User@123", "User@1234", "User@12345"]
        accepted_admin_pwd = ["Admin@123", "Admin@1234", "Admin@12345"]
        if username == "User" and password in accepted_user_pwd:
            session["user"] = username
            return redirect(url_for("user_dashboard"))
        elif username == "Admin" and password in accepted_admin_pwd:
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))
    
    return render_template("login.html")

# User Dashboard    
@app.route("/user_dashboard", methods=["GET", "POST"])
def user_dashboard():
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    cursor.execute("SHOW TABLES")
    # [('Honda',), ('Toyota',), ('Suzuki',)]
    makes = [row[0].title() for row in cursor.fetchall()]
    # Same as
    # for row in cursor.fetchall():
    #     models.append(row[0])

    selected_make = request.form.get("make")
    selected_model = request.form.get("model")
    selected_variant = request.form.get("variant")
    selected_part = request.form.get("part")
    modelyear = request.form.get("modelyear")
    quantity = request.form.get("quantity")
    billing_address = request.form.get("address")

    models, variants, parts = [], [], []
    unit_price = None
    total = None

    if selected_make:
        cursor.execute(f"SELECT DISTINCT Model FROM {selected_make}")
        models = [row[0] for row in cursor.fetchall()]

    if selected_make and selected_model:
        cursor.execute(f"SELECT DISTINCT Variant FROM {selected_make} WHERE Model = %s", (selected_model,))
        variants = [row[0] for row in cursor.fetchall()]

    if selected_make and selected_model and selected_variant:
        cursor.execute(f"SELECT DISTINCT Part FROM {selected_make} WHERE Model = %s AND Variant = %s",
                       (selected_model, selected_variant))
        parts = [row[0] for row in cursor.fetchall()]

    if selected_make and selected_model and selected_variant and selected_part:
        cursor.execute(f"SELECT Unit_Price FROM {selected_make} WHERE Model = %s AND Variant = %s AND Part = %s",
                       (selected_model, selected_variant, selected_part))
        result = cursor.fetchone() 
        if result:
            unit_price = result[0]

    if unit_price and quantity:
        total = round(unit_price * int(quantity) * 1.18, 2)
            

    if selected_make and selected_model and selected_variant and selected_part and modelyear and quantity and billing_address:
        query = f"SELECT * FROM {selected_make} WHERE Model = %s AND Variant = %s AND Part = %s"
        cursor.execute(query, (selected_model, selected_variant, selected_part))
        result = cursor.fetchall() 
        for row in result:
            a, b, c, d, e = row
            available_qty = d

        if available_qty is None:
            flash("Error fetching available quantity.", "danger")
        elif int(quantity) > available_qty:
            flash(f"Only {available_qty} units available in stock. Please enter a lower quantity.", "warning")
        else:
            cursor.execute(f"""
            UPDATE {selected_make}
            SET Quantity = Quantity - %s
            WHERE Model = %s AND Variant = %s AND Part = %s
            """, (quantity, selected_model, selected_variant, selected_part))
            conn.commit()
            flash(f"Thank you for placing the order. Total Price (incl. GST 18%): ₹{total}. Details of the order will be sent to your registered email.", "success")

            return redirect(url_for("user_dashboard"))

    return render_template("user_dashboard.html",
                           makes=makes,
                           selected_make=selected_make,
                           models=models,
                           selected_model=selected_model,
                           variants=variants,
                           selected_variant=selected_variant,
                           parts=parts,
                           selected_part=selected_part,
                           unit_price=unit_price,
                           total=total,
                           modelyear=modelyear,
                           quantity=quantity,
                           billing_address=billing_address)

# Admin Dashboard
@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "admin" not in session:
        flash("Please log in as admin first.", "warning")
        return redirect(url_for("login"))

    cursor.execute("SHOW TABLES")
    makes = [row[0].title() for row in cursor.fetchall()]

    # Determining active tab, default = "purchase"
    active_tab = request.args.get("tab", "purchase")

    make = model = variant = part = modelyear = quantity = billing_address = customer_name = ""
    models, variants, parts = [], [], []
    unit_price = None
    total = None
    available_qty = None
    unit_price = None
    operation = None
    current_price = None

    # Purchase operation
    if active_tab == "purchase" and request.method == "POST":
        customer_name = request.form.get("customer_name")
        make = request.form.get("make")
        model = request.form.get("model")
        variant = request.form.get("variant")
        part = request.form.get("part")
        modelyear = request.form.get("modelyear")
        quantity = request.form.get("quantity")
        billing_address = request.form.get("address")

        if make:
            cursor.execute(f"SELECT DISTINCT Model FROM {make}")
            models = [row[0] for row in cursor.fetchall()]

        if make and model:
            cursor.execute(f"SELECT DISTINCT Variant FROM {make} WHERE Model = %s", (model,))
            variants = [row[0] for row in cursor.fetchall()]

        if make and model and variant:
            cursor.execute(f"SELECT DISTINCT Part FROM {make} WHERE Model = %s AND Variant = %s",
                        (model, variant))
            parts = [row[0] for row in cursor.fetchall()]

        if make and model and variant and part:
            cursor.execute(f"SELECT Unit_Price FROM {make} WHERE Model = %s AND Variant = %s AND Part = %s",
                        (model, variant, part))
            result = cursor.fetchone()
            if result:
                unit_price = result[0]

        if unit_price and quantity:
                total = round(unit_price * int(quantity) * 1.18, 2)  

        if make and model and variant and part and modelyear and quantity and billing_address:
            query = f"SELECT * FROM {make} WHERE Model = %s AND Variant = %s AND Part = %s"
            cursor.execute(query, (model, variant, part))
            result = cursor.fetchall()
            for row in result:
                a, b, c, d, e = row
                available_qty = d

            if available_qty is None:
                flash("Error fetching available quantity.", "danger")
            elif int(quantity) > available_qty:
                if available_qty == 0:
                    flash("This part is currently out of stock.", "warning")
                else:
                    flash(f"Only {available_qty} units available in stock. Please enter a lower quantity.", "warning")
            else:
                cursor.execute(f"""
                UPDATE {make}
                SET Quantity = Quantity - %s
                WHERE Model = %s AND Variant = %s AND Part = %s
                """, (quantity, model, variant, part))

                conn.commit()
                flash(f"Order placed successfully for {customer_name}. Total Price (incl. GST 18%): ₹{total}. Details of the order will be sent to your registered email.", "success")

                return redirect(url_for("admin_dashboard"))

    
    # Check Quantity operation
    
    elif active_tab == "check_stock" and request.method == "POST":
        make = request.form.get("make")
        model = request.form.get("model")
        variant = request.form.get("variant")
        part = request.form.get("part")

        if make:
            cursor.execute(f"SELECT DISTINCT Model FROM {make}")
            models = [row[0] for row in cursor.fetchall()]

        if make and model:
            cursor.execute(f"SELECT DISTINCT Variant FROM {make} WHERE Model = %s", (model,))
            variants = [row[0] for row in cursor.fetchall()]

        if make and model and variant:
            cursor.execute(f"SELECT DISTINCT Part FROM {make} WHERE Model = %s AND Variant = %s",
                        (model, variant))
            parts = [row[0] for row in cursor.fetchall()]

        if make and model and variant and part:
            query = f"SELECT * FROM {make} WHERE Model = %s AND Variant = %s AND Part = %s"
            cursor.execute(query, (model, variant, part))
            result = cursor.fetchall()
            for row in result:
                a, b, c, d, e = row
                available_qty = d
                unit_price = e

                if available_qty == 0:
                    flash("This part is currently out of stock.", "warning")

    
    #Update Stock Operation
    elif active_tab == "update_stock" and request.method == "POST":
        operation = request.form.get("operation")
        make = request.form.get("make")
        model = request.form.get("model")
        variant = request.form.get("variant")
        part = request.form.get("part")
        quantity = request.form.get("quantity")
        price = request.form.get("price")

        if make:
            cursor.execute(f"SELECT DISTINCT Model FROM {make}")
            models = [row[0] for row in cursor.fetchall()]

        if make and model:
            cursor.execute(f"SELECT DISTINCT Variant FROM {make} WHERE Model = %s", (model,))
            variants = [row[0] for row in cursor.fetchall()]

        if make and model and variant:
            cursor.execute(f"SELECT DISTINCT Part FROM {make} WHERE Model = %s AND Variant = %s", (model, variant))
            parts = [row[0] for row in cursor.fetchall()]

        # Add Part Operation
        if operation == "add":
            if  make and model and variant and part and quantity and price:
                    cursor.execute(f"INSERT INTO {make} (Model, Variant, Part, Quantity, Unit_Price) VALUES (%s, %s, %s, %s, %s)",
                                    (model, variant, part, quantity, price))
                    conn.commit()
                    flash(f"Part {part} added successfully for {make} {model} {variant}. Quantity: {quantity}, Unit Price: ₹{price}.", "success")
                    return redirect(url_for("admin_dashboard"))

        # Delete Part Operation
        elif operation == "delete":
            if make and model and variant and part:
                cursor.execute(f"DELETE FROM {make} WHERE Model = %s AND Variant = %s AND Part = %s",
                                    (model, variant, part))
                conn.commit()
                flash(f"Part {part} deleted successfully for {make} {model} {variant}.", "success")
                return redirect(url_for("admin_dashboard"))

        # Update Quantity Operation:
        elif operation == "update_quantity":
            if make and model and variant and part:
                cursor.execute(f"SELECT Quantity FROM {make} WHERE Model = %s AND Variant = %s AND Part = %s",
                                (model, variant, part))
                result = cursor.fetchone()
                available_qty = result[0]
            
            if make and model and variant and part and quantity:
                cursor.execute(f"UPDATE {make} SET Quantity = %s WHERE Model = %s AND Variant = %s AND Part = %s",
                                    (quantity, model, variant, part))
                conn.commit()
                flash(f"Current available quantity for {part} is {available_qty}. Quantity updated successfully to {quantity}.", "success")
                return redirect(url_for("admin_dashboard"))

        # Update Price Operation:
        elif operation == "update_price":
            if make and model and variant and part:
                cursor.execute(f"SELECT Unit_Price FROM {make} WHERE Model = %s AND Variant = %s AND Part = %s",
                                (model, variant, part))
                result = cursor.fetchone()
                current_price = result[0]

            if make and model and variant and part and price:
                cursor.execute(f"UPDATE {make} SET Unit_Price = %s WHERE Model = %s AND Variant = %s AND Part = %s",
                                    (price, model, variant, part))
                conn.commit()
                flash(f"Current price for {part} is ₹{current_price}. Price updated successfully to ₹{price}.", "success")
                return redirect(url_for("admin_dashboard"))

    return render_template("admin_dashboard.html",
                        active_tab=active_tab,
                        # For Purchase Tab
                        customer_name=customer_name,
                        makes=makes,
                        selected_make=make,
                        selected_model=model,
                        selected_variant=variant,
                        selected_part=part,
                        models=models,
                        variants=variants,
                        parts=parts,
                        total=total,
                        modelyear=modelyear,
                        quantity=quantity,
                        unit_price=unit_price,
                        billing_address=billing_address,
                        # For Check Stock Tab
                        available_qty=available_qty,
                        # For Update Stock Tab
                        operation=operation,
                        make=make,
                        model=model,
                        variant=variant,
                        part=part,
                        price=unit_price,
                        current_price=current_price,
                        current_quantity=available_qty,
                        )

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True, port=8000)