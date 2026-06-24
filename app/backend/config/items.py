# Food Sales Reference Data

STORES = [
    {"s_store_sk": 1, "s_store_id": "STORE_001", "s_store_name": "Downtown Hub", "s_city": "Seattle", "s_state": "WA"},
    {"s_store_sk": 2, "s_store_id": "STORE_002", "s_store_name": "U-District", "s_city": "Seattle", "s_state": "WA"},
]

PREDICTION_SLOTS = [
    {"slot": 1, "start": "00:00", "end": "02:00", "label": "12–2 AM"},
    {"slot": 2, "start": "02:00", "end": "04:00", "label": "2–4 AM"},
    {"slot": 3, "start": "04:00", "end": "06:00", "label": "4–6 AM"},
    {"slot": 4, "start": "06:00", "end": "08:00", "label": "6–8 AM"},
    {"slot": 5, "start": "08:00", "end": "10:00", "label": "8–10 AM"},
    {"slot": 6, "start": "10:00", "end": "12:00", "label": "10–12 PM"},
    {"slot": 7, "start": "12:00", "end": "14:00", "label": "12–2 PM"},
    {"slot": 8, "start": "14:00", "end": "16:00", "label": "2–4 PM"},
    {"slot": 9, "start": "16:00", "end": "18:00", "label": "4–6 PM"},
    {"slot": 10, "start": "18:00", "end": "20:00", "label": "6–8 PM"},
    {"slot": 11, "start": "20:00", "end": "22:00", "label": "8–10 PM"},
    {"slot": 12, "start": "22:00", "end": "24:00", "label": "10–12 AM"},
]

ITEMS = {
    "categories": [
        {
            "id": "item-burgers",
            "name": "Burgers",
            "subtypes": [
                {"id": "cat-beef", "name": "Classic Beef"},
                {"id": "cat-chicken", "name": "Crispy Chicken"},
                {"id": "cat-veggie", "name": "Veggie Black Bean"},
            ],
        },
        {
            "id": "item-pizza",
            "name": "Pizza",
            "subtypes": [
                {"id": "cat-pepperoni", "name": "Pepperoni"},
                {"id": "cat-margherita", "name": "Margherita"},
                {"id": "cat-hawaiian", "name": "Hawaiian"},
            ],
        },
        {
            "id": "item-salads",
            "name": "Salads",
            "subtypes": [
                {"id": "cat-caesar", "name": "Caesar"},
                {"id": "cat-garden", "name": "Garden Fresh"},
                {"id": "cat-cobb", "name": "Cobb"},
            ],
        },
        {
            "id": "item-drinks",
            "name": "Drinks",
            "subtypes": [
                {"id": "cat-cola", "name": "Cola"},
                {"id": "cat-lemonade", "name": "Lemonade"},
                {"id": "cat-water", "name": "Bottled Water"},
            ],
        },
        {
            "id": "item-sides",
            "name": "Sides",
            "subtypes": [
                {"id": "cat-fries", "name": "French Fries"},
                {"id": "cat-onionrings", "name": "Onion Rings"},
                {"id": "cat-mozzsticks", "name": "Mozzarella Sticks"},
            ],
        },
    ]
}
