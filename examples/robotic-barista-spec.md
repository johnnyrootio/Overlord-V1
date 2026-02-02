
## Coding Test Product Spec: Automated Barista CLI

### 1) Goal

Build a command-line application that simulates an automated coffee barista. Users can:

* Define recipes (drink name + ingredients + steps)
* Place drink orders
* Track inventory (ingredients on hand)
* Produce a brew plan (what the machine will do) or fail with clear reasons

The system does not control real hardware. It only models behavior and state.

### 2) Core Concepts and Constraints

**Entities**

* **Ingredient**: name, unit (ml, g, count), optional “isPerishable” flag
* **InventoryItem**: ingredient, quantityAvailable
* **Recipe**: id, name, ingredientsRequired (ingredient + quantity), steps (ordered list), brewTimeSeconds (optional)
* **Order**: id, recipeId, size (S/M/L), status (PLACED, VALIDATED, BREWING, COMPLETED, FAILED), timestamps

**Rules**

* Inventory must be checked before brewing.
* Brewing consumes inventory.
* If inventory is insufficient, order fails and does not consume inventory.
* Sizes scale ingredient quantities:

  * S = 1.0x, M = 1.5x, L = 2.0x
* Steps are informational text, but must be returned in the brew plan in order.
* Concurrency is not required, but code should not make it impossible (for example, avoid global mutable state that would break ordering).

### 3) CLI Requirements

Implement a single executable command (language of choice) with subcommands.

**Commands**

1. `inventory list`

* Output all ingredients and quantities.

2. `inventory add <ingredient> <quantity> <unit>`

* Adds to inventory (ingredient created if new).
* Units must match existing ingredient unit if ingredient exists.

3. `recipes list`

* List recipe id + name.

4. `recipes show <recipeId>`

* Show full recipe: ingredients, steps, base quantities.

5. `recipes add --name "<name>" --ingredient "<ingredient>:<qty><unit>" [--ingredient ...] --step "<text>" [--step ...]`

* Creates a new recipe.
* At least 1 ingredient and 1 step.

6. `order place <recipeId> --size S|M|L`

* Creates an order in PLACED state and prints the order id.

7. `order validate <orderId>`

* Checks inventory and transitions to VALIDATED or FAILED.
* If FAILED, include a human-readable reason and missing ingredients list.

8. `order brew <orderId>`

* Only allowed from VALIDATED.
* Produces a “brew plan” (steps + computed scaled ingredient usage).
* Consumes inventory and transitions to COMPLETED.
* If inventory changed since validation and is now insufficient, transition to FAILED without consuming anything.

9. `orders list [--status <status>]`

* List orders with id, recipe name, size, status, created timestamp.

### 4) Output Format

Human-readable text is fine, but must be consistent.

* Errors must print a clear message and exit with non-zero code.
* Success returns zero.

Example snippet for brew plan:

* Order: 123 (Latte, M)
* Use:

  * espresso: 45ml
  * milk: 225ml
* Steps:

  1. Grind beans
  2. Pull espresso shot
  3. Steam milk
  4. Combine and serve

### 5) Persistence Requirements

State must persist across runs:

* Inventory
* Recipes
* Orders

Allowed approaches:

* JSON or SQLite file in a local data directory
* In-memory is not sufficient

### 6) Non-Functional Requirements

* Code must be modular (separate domain logic from CLI parsing and persistence).
* Include a small test suite that covers:

  * size scaling
  * validation fails with correct missing items
  * brew consumes inventory exactly once
  * brew fails if inventory changed after validation
* Provide a short README with:

  * how to run
  * example command sequence
  * assumptions

### 7) Suggested Architecture (Not Mandatory, But Recommended)

* `domain/` (entities + rules)
* `services/` (recipe service, inventory service, order service)
* `storage/` (repository interfaces + JSON/SQLite implementation)
* `cli/` (command parsing + printing)
* `tests/`

### 8) Acceptance Criteria

A submission is considered complete when:

* All commands work as described
* Persistence works across app restarts
* Order lifecycle and inventory rules are enforced
* Tests pass and cover the core behaviors
* Reasonable error handling and input validation exist

### 9) Bonus (Optional)

Implement one of these (only if time):

* `inventory set <ingredient> <quantity><unit>` (overwrite)
* Support perishable ingredients with an expiry date, and validation rejects expired stock
* Add `order cancel <orderId>` (only PLACED/VALIDATED)

If you want, I can also generate:

* a candidate handout version (shorter, 1 page)
* a grading rubric (correctness, architecture, tests, ergonomics)
* a hidden “edge-case” list for interviewers (unit mismatch, double-brew, invalid transitions, etc.)
