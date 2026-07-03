CREATE TABLE sonuDhabaGeneral (
    restaurant_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    restaurant_title VARCHAR(255) NOT NULL,
    is_open BOOLEAN NOT NULL DEFAULT TRUE,
    customer_rating DECIMAL(2, 1) NULL
);

CREATE TABLE sonuDhabaAddress (
    restaurant_id INT UNSIGNED NOT NULL,
    city VARCHAR(255) NULL,
    postal VARCHAR(15) NULL,
    street_address VARCHAR(500) NULL,
    FOREIGN KEY (restaurant_id) REFERENCES sonuDhabaGeneral(restaurant_id)
);

CREATE TABLE sonuMenuGeneral (
    food_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    food_title VARCHAR(255) NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    restaurant_ref INT UNSIGNED NOT NULL,
    cost_price DECIMAL(10, 2) NULL,
    FOREIGN KEY (restaurant_ref) REFERENCES sonuDhabaGeneral(restaurant_id)
);

CREATE TABLE sonuMenuRatings (
    food_id BIGINT UNSIGNED NOT NULL,
    food_rating DECIMAL(2, 1) NULL,
    FOREIGN KEY (food_id) REFERENCES sonuMenuGeneral(food_id)
);

INSERT INTO sonuDhabaGeneral (restaurant_title, is_open, customer_rating)
VALUES
('Sonu Dhaba Classic', TRUE, 4.5),
('Sonu Dhaba Express', TRUE, 4.0),
('Sonu Dhaba Deluxe', FALSE, 4.8);

INSERT INTO sonuDhabaAddress (restaurant_id, city, postal, street_address)
VALUES
(1, 'Mumbai', '400001', '123 Marine Drive'),
(2, 'Delhi', '110001', '456 Connaught Place'),
(3, 'Bangalore', '560001', '789 MG Road');

INSERT INTO sonuMenuGeneral (food_title, is_available, restaurant_ref, cost_price)
VALUES
('Butter Chicken', TRUE, 1, 299.99),
('Paneer Tikka', TRUE, 1, 199.99),
('Biryani', TRUE, 2, 249.50),
('Tandoori Roti', TRUE, 2, 20.00),
('Masala Dosa', FALSE, 3, 150.00),
('Idli Sambar', TRUE, 3, 120.00);

INSERT INTO sonuMenuRatings (food_id, food_rating)
VALUES
(1, 4.7),
(2, 4.5),
(3, 4.3),
(4, 4.2),
(5, 4.1),
(6, 4.6);
