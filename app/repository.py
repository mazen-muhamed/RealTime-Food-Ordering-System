from sqlalchemy.orm import Session
from sqlalchemy import text


# =========================
# Users
# =========================

def get_user_by_email(
    db: Session,
    email: str
):
    result = db.execute(
        text("""
            SELECT
                id,
                username,
                email,
                phone_number,
                password
            FROM users
            WHERE email = :email
        """),
        {
            "email": email
        }
    ).fetchone()

    if not result:
        return None

    return dict(result._mapping)


def get_user_by_phone(
    db: Session,
    phone_number: str
):
    result = db.execute(
        text("""
            SELECT
                id,
                username,
                email,
                phone_number,
                password
            FROM users
            WHERE phone_number = :phone_number
        """),
        {
            "phone_number": phone_number
        }
    ).fetchone()

    if not result:
        return None

    return dict(result._mapping)


def get_user_by_id(
    db: Session,
    user_id: int
):
    result = db.execute(
        text("""
            SELECT
                id,
                username,
                email,
                phone_number,
                password
            FROM users
            WHERE id = :user_id
        """),
        {
            "user_id": user_id
        }
    ).fetchone()

    if not result:
        return None

    return dict(result._mapping)


def create_user(
    db: Session,
    username: str,
    email: str,
    phone_number: str,
    hashed_password: str
):
    result = db.execute(
        text("""
            INSERT INTO users (
                username,
                email,
                phone_number,
                password
            )
            VALUES (
                :username,
                :email,
                :phone_number,
                :password
            )
        """),
        {
            "username": username,
            "email": email,
            "phone_number": phone_number,
            "password": hashed_password
        }
    )

    db.commit()

    user_id = result.lastrowid

    return get_user_by_id(
        db,
        user_id
    )


# =========================
# Restaurants
# =========================

def get_restaurant(
    db: Session,
    restaurant_id: int
):
    result = db.execute(
        text("""
            SELECT
                id,
                name,
                is_available,
                max_concurrent_orders,
                current_order_count
            FROM restaurants
            WHERE id = :restaurant_id
        """),
        {
            "restaurant_id": restaurant_id
        }
    ).fetchone()

    if not result:
        return None

    return dict(result._mapping)


def get_restaurants(
    db: Session
):
    result = db.execute(
        text("""
            SELECT
                id,
                name,
                is_available,
                max_concurrent_orders,
                current_order_count
            FROM restaurants
            ORDER BY id
        """)
    ).fetchall()

    return [
        dict(row._mapping)
        for row in result
    ]


# =========================
# Restaurant Menu
# =========================

def get_restaurant_menu(
    db: Session,
    restaurant_id: int
):
    # Menu table is not defined yet
    # in the current schema.py.

    return []


# =========================
# Orders
# =========================

def create_order(
    db: Session,
    restaurant_id: int,
    customer_id: int,
    state: str
):
    result = db.execute(
        text("""
            INSERT INTO orders (
                restaurant_id,
                customer_id,
                state
            )
            VALUES (
                :restaurant_id,
                :customer_id,
                :state
            )
        """),
        {
            "restaurant_id": restaurant_id,
            "customer_id": customer_id,
            "state": state
        }
    )

    db.commit()

    order_id = result.lastrowid

    return get_order(
        db,
        order_id
    )


def get_order(
    db: Session,
    order_id: int
):
    result = db.execute(
        text("""
            SELECT
                id,
                restaurant_id,
                customer_id,
                state,
                created_at,
                updated_at
            FROM orders
            WHERE id = :order_id
        """),
        {
            "order_id": order_id
        }
    ).fetchone()

    if not result:
        return None

    return dict(result._mapping)


def get_orders(
    db: Session,
    limit: int = 50
):
    result = db.execute(
        text("""
            SELECT
                id,
                restaurant_id,
                customer_id,
                state,
                created_at,
                updated_at
            FROM orders
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {
            "limit": limit
        }
    ).fetchall()

    return [
        dict(row._mapping)
        for row in result
    ]


def update_order_state(
    db: Session,
    order_id: int,
    new_state: str
):
    db.execute(
        text("""
            UPDATE orders
            SET state = :state
            WHERE id = :order_id
        """),
        {
            "state": new_state,
            "order_id": order_id
        }
    )

    db.commit()

    return get_order(
        db,
        order_id
    )


# =========================
# Order State Log
# =========================

def create_order_state_log(
    db: Session,
    order_id: int,
    from_state,
    to_state: str
):
    result = db.execute(
        text("""
            INSERT INTO order_state_log (
                order_id,
                from_state,
                to_state
            )
            VALUES (
                :order_id,
                :from_state,
                :to_state
            )
        """),
        {
            "order_id": order_id,
            "from_state": from_state,
            "to_state": to_state
        }
    )

    db.commit()

    return result.lastrowid

