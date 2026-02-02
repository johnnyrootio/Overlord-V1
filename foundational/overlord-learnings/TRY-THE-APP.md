# How to Try the Robotic Barista App

These instructions are for running the **robotic-barista** CLI app (the app lives in the separate repo `johnnyrootio/robotic-barista`).

---

## 1. Prerequisites

- **Python 3.11+**
- **Git**
- Optional: **[uv](https://github.com/astral-sh/uv)** (faster installs) or **pip** + **venv**

Check Python:

```bash
python3 --version   # or: python --version
```

---

## 2. Get the app

Clone the robotic-barista repository (if you don’t already have it):

```bash
git clone https://github.com/johnnyrootio/robotic-barista.git
cd robotic-barista
```

---

## 3. Install

**Option A – Install script (if present)**

```bash
./scripts/install.sh
```

**Option B – With uv**

```bash
uv sync
```

**Option C – With pip (editable install)**

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

---

## 4. Verify the CLI

You should have the `barista` command (and/or `python -m robotic_barista`):

```bash
barista --help
```

You should see the top-level command and subcommands: `inventory`, `recipes`, `order`, `orders`.

---

## 5. Example: full flow

Run these in order to add stock, define a recipe, place an order, validate it, brew it, and list orders.

**Set up inventory**

```bash
barista inventory add espresso 100 ml
barista inventory add milk 500 ml
barista inventory list
```

**Add a recipe**

```bash
barista recipes add --name "Latte" \
  --ingredient "espresso:30ml" \
  --ingredient "milk:150ml" \
  --step "Grind beans" \
  --step "Pull espresso shot" \
  --step "Steam milk" \
  --step "Combine and serve"
barista recipes list
barista recipes show <recipe-id>   # use id from list
```

**Place an order**

```bash
barista order place <recipe-id> --size M
```

Copy the printed **order id**.

**Validate then brew**

```bash
barista order validate <order-id>
barista order brew <order-id>
```

**List orders**

```bash
barista orders list
barista orders list --status COMPLETED
```

---

## 6. Data location

State is stored under a local data directory (e.g. a `data/` folder or similar in the repo or under your home directory). Restarting the app or running the commands again uses the same inventory, recipes, and orders.

---

## 7. Run tests (optional)

From the `robotic-barista` repo root:

```bash
./scripts/check.sh
# or
pytest
```

---

## Quick reference

| What you want       | Command |
|---------------------|--------|
| List inventory      | `barista inventory list` |
| Add to inventory    | `barista inventory add <ingredient> <qty> <unit>` |
| List recipes        | `barista recipes list` |
| Show one recipe     | `barista recipes show <id>` |
| Add recipe          | `barista recipes add --name "..." --ingredient "..." --step "..."` |
| Place order         | `barista order place <recipe-id> --size S\|M\|L` |
| Validate order      | `barista order validate <order-id>` |
| Brew order          | `barista order brew <order-id>` |
| List orders         | `barista orders list [--status <status>]` |

Sizes scale ingredients: **S** = 1.0×, **M** = 1.5×, **L** = 2.0×.
