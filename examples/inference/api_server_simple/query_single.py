#
# Copyright 2023 The LLM-on-Ray Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import requests
import argparse
from typing import Dict, Union

test_propmt = """

### Instructions:
        Your task is convert a question into a SQL query, given a MySQL database schema.
        Adhere to these rules:
        - **Deliberately go through the question and database schema word by word** to appropriately answer the question
        - **Use Table Aliases** to prevent ambiguity. For example, `SELECT table1.col1, table2.col1 FROM table1 JOIN table2 ON table1.id = table2.id`.
        - When creating a ratio, always cast the numerator as float
        - Use LIKE instead of ilike
        - Only generate the SQL query, no additional text is required
        - Generate SQL queries for MySQL database

        ### Input:
        Generate a SQL query that answers the question `How many distinct actors last names are there?`.
        This query will run on a database whose schema is represented in this string:
        CREATE TABLE actor (
  actor_id numeric NOT NULL ,
  first_name VARCHAR(45) NOT NULL,
  last_name VARCHAR(45) NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (actor_id)
  )
;
CREATE TABLE address (
  address_id int NOT NULL,
  address VARCHAR(50) NOT NULL,
  address2 VARCHAR(50) DEFAULT NULL,
  district VARCHAR(20) NOT NULL,
  city_id INT  NOT NULL,
  postal_code VARCHAR(10) DEFAULT NULL,
  phone VARCHAR(20) NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (address_id),
  CONSTRAINT fk_address_city FOREIGN KEY (city_id) REFERENCES city (city_id) ON DELETE NO ACTION ON UPDATE CASCADE
)
;
CREATE TABLE category (
  category_id SMALLINT NOT NULL,
  name VARCHAR(25) NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (category_id)
)
;
CREATE TABLE city (
  city_id int NOT NULL,
  city VARCHAR(50) NOT NULL,
  country_id SMALLINT NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (city_id),
  CONSTRAINT fk_city_country FOREIGN KEY (country_id) REFERENCES country (country_id) ON DELETE NO ACTION ON UPDATE CASCADE
)
;
CREATE TABLE country (
  country_id SMALLINT NOT NULL,
  country VARCHAR(50) NOT NULL,
  last_update TIMESTAMP,
  PRIMARY KEY  (country_id)
)
;
CREATE TABLE customer (
  customer_id INT NOT NULL,
  store_id INT NOT NULL,
  first_name VARCHAR(45) NOT NULL,
  last_name VARCHAR(45) NOT NULL,
  email VARCHAR(50) DEFAULT NULL,
  address_id INT NOT NULL,
  active CHAR(1) DEFAULT 'Y' NOT NULL,
  create_date TIMESTAMP NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (customer_id),
  CONSTRAINT fk_customer_store FOREIGN KEY (store_id) REFERENCES store (store_id) ON DELETE NO ACTION ON UPDATE CASCADE,
  CONSTRAINT fk_customer_address FOREIGN KEY (address_id) REFERENCES address (address_id) ON DELETE NO ACTION ON UPDATE CASCADE
)
;
CREATE TABLE film (
  film_id int NOT NULL,
  title VARCHAR(255) NOT NULL,
  description BLOB SUB_TYPE TEXT DEFAULT NULL,
  release_year VARCHAR(4) DEFAULT NULL,
  language_id SMALLINT NOT NULL,
  original_language_id SMALLINT DEFAULT NULL,
  rental_duration SMALLINT  DEFAULT 3 NOT NULL,
  rental_rate DECIMAL(4,2) DEFAULT 4.99 NOT NULL,
  length SMALLINT DEFAULT NULL,
  replacement_cost DECIMAL(5,2) DEFAULT 19.99 NOT NULL,
  rating VARCHAR(10) DEFAULT 'G',
  special_features VARCHAR(100) DEFAULT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (film_id),
  CONSTRAINT CHECK_special_features CHECK(special_features is null or
                                                           special_features like '%Trailers%' or
                                                           special_features like '%Commentaries%' or
                                                           special_features like '%Deleted Scenes%' or
                                                           special_features like '%Behind the Scenes%'),
  CONSTRAINT CHECK_special_rating CHECK(rating in ('G','PG','PG-13','R','NC-17')),
  CONSTRAINT fk_film_language FOREIGN KEY (language_id) REFERENCES language (language_id) ,
  CONSTRAINT fk_film_language_original FOREIGN KEY (original_language_id) REFERENCES language (language_id)
)
;
CREATE TABLE film_actor (
  actor_id INT NOT NULL,
  film_id  INT NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (actor_id,film_id),
  CONSTRAINT fk_film_actor_actor FOREIGN KEY (actor_id) REFERENCES actor (actor_id) ON DELETE NO ACTION ON UPDATE CASCADE,
  CONSTRAINT fk_film_actor_film FOREIGN KEY (film_id) REFERENCES film (film_id) ON DELETE NO ACTION ON UPDATE CASCADE
)
;
CREATE TABLE film_category (
  film_id INT NOT NULL,
  category_id SMALLINT  NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY (film_id, category_id),
  CONSTRAINT fk_film_category_film FOREIGN KEY (film_id) REFERENCES film (film_id) ON DELETE NO ACTION ON UPDATE CASCADE,
  CONSTRAINT fk_film_category_category FOREIGN KEY (category_id) REFERENCES category (category_id) ON DELETE NO ACTION ON UPDATE CASCADE
)
;
CREATE TABLE film_text (
  film_id SMALLINT NOT NULL,
  title VARCHAR(255) NOT NULL,
  description BLOB SUB_TYPE TEXT,
  PRIMARY KEY  (film_id)
)
;
CREATE TABLE inventory (
  inventory_id INT NOT NULL,
  film_id INT NOT NULL,
  store_id INT NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (inventory_id),
  CONSTRAINT fk_inventory_store FOREIGN KEY (store_id) REFERENCES store (store_id) ON DELETE NO ACTION ON UPDATE CASCADE,
  CONSTRAINT fk_inventory_film FOREIGN KEY (film_id) REFERENCES film (film_id) ON DELETE NO ACTION ON UPDATE CASCADE
)
;
CREATE TABLE language (
  language_id SMALLINT NOT NULL ,
  name CHAR(20) NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY (language_id)
)
;
CREATE TABLE payment (
  payment_id int NOT NULL,
  customer_id INT  NOT NULL,
  staff_id SMALLINT NOT NULL,
  rental_id INT DEFAULT NULL,
  amount DECIMAL(5,2) NOT NULL,
  payment_date TIMESTAMP NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (payment_id),
  CONSTRAINT fk_payment_rental FOREIGN KEY (rental_id) REFERENCES rental (rental_id) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_payment_customer FOREIGN KEY (customer_id) REFERENCES customer (customer_id) ,
  CONSTRAINT fk_payment_staff FOREIGN KEY (staff_id) REFERENCES staff (staff_id)
)
;
CREATE TABLE rental (
  rental_id INT NOT NULL,
  rental_date TIMESTAMP NOT NULL,
  inventory_id INT  NOT NULL,
  customer_id INT  NOT NULL,
  return_date TIMESTAMP DEFAULT NULL,
  staff_id SMALLINT  NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY (rental_id),
  CONSTRAINT fk_rental_staff FOREIGN KEY (staff_id) REFERENCES staff (staff_id) ,
  CONSTRAINT fk_rental_inventory FOREIGN KEY (inventory_id) REFERENCES inventory (inventory_id) ,
  CONSTRAINT fk_rental_customer FOREIGN KEY (customer_id) REFERENCES customer (customer_id)
)
;
CREATE TABLE staff (
  staff_id SMALLINT NOT NULL,
  first_name VARCHAR(45) NOT NULL,
  last_name VARCHAR(45) NOT NULL,
  address_id INT NOT NULL,
  picture BLOB DEFAULT NULL,
  email VARCHAR(50) DEFAULT NULL,
  store_id INT NOT NULL,
  active SMALLINT DEFAULT 1 NOT NULL,
  username VARCHAR(16) NOT NULL,
  password VARCHAR(40) DEFAULT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (staff_id),
  CONSTRAINT fk_staff_store FOREIGN KEY (store_id) REFERENCES store (store_id) ON DELETE NO ACTION ON UPDATE CASCADE,
  CONSTRAINT fk_staff_address FOREIGN KEY (address_id) REFERENCES address (address_id) ON DELETE NO ACTION ON UPDATE CASCADE
)
;
CREATE TABLE store (
  store_id INT NOT NULL,
  manager_staff_id SMALLINT NOT NULL,
  address_id INT NOT NULL,
  last_update TIMESTAMP NOT NULL,
  PRIMARY KEY  (store_id),
  CONSTRAINT fk_store_staff FOREIGN KEY (manager_staff_id) REFERENCES staff (staff_id) ,
  CONSTRAINT fk_store_address FOREIGN KEY (address_id) REFERENCES address (address_id)
);

        ### Response:
        Based on your instructions, here is the SQL query I have generated to answer the question `How many distinct actors last names are there?`:
        ```sql
"""
parser = argparse.ArgumentParser(
    description="Example script to query with single request", add_help=True
)
parser.add_argument(
    "--model_endpoint",
    default="http://127.0.0.1:8000",
    type=str,
    help="Deployed model endpoint.",
)
parser.add_argument(
    "--streaming_response",
    default=False,
    action="store_true",
    help="Whether to enable streaming response.",
)
parser.add_argument(
    "--max_new_tokens", default=256, help="The maximum numbers of tokens to generate."
)
parser.add_argument(
    "--temperature",
    default=0.5,
    help="The value used to modulate the next token probabilities.",
)
parser.add_argument(
    "--top_p",
    default=0.3,
    help="If set to float < 1, only the smallest set of most probable tokens \
        with probabilities that add up to `Top p` or higher are kept for generation.",
)
parser.add_argument(
    "--top_k",
    default=None,
    help="The number of highest probability vocabulary tokens to keep \
        for top-k-filtering.",
)

args = parser.parse_args()
prompt = "Once upon a time,"
config: Dict[str, Union[int, float]] = {}
if args.max_new_tokens:
    config["max_new_tokens"] = int(args.max_new_tokens)
if args.temperature:
    config["temperature"] = float(args.temperature)
if args.top_p:
    config["top_p"] = float(args.top_p)
if args.top_k:
    config["top_k"] = float(args.top_k)
prompt = test_propmt
sample_input = {"text": prompt, "config": config, "stream": args.streaming_response}

proxies = {"http": None, "https": None}
outputs = requests.post(
    args.model_endpoint,
    proxies=proxies,  # type: ignore
    json=sample_input,
    stream=args.streaming_response,
)

try:
    outputs.raise_for_status()
    if args.streaming_response:
        for output in outputs.iter_content(chunk_size=None, decode_unicode=True):
            print(output, end="", flush=True)
        print()
    else:
        print(outputs.text, flush=True)
except Exception as e:
    print(e)
