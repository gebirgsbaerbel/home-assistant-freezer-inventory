# Freezer Inventory

A Home Assistant custom integration that turns a todo list into a freezer inventory tracker — with a built-in Lovelace card.

## Features

- Reads items from any Home Assistant todo list
- Tracks portion counts (stored in the item description) and expiration dates (stored as the due date)
- Sorts items by expiration date, then portions
- Built-in Lovelace card — no extra card dependencies needed
- `freezer_inventory.freezer_minus` service to decrement portions with one tap

## Installation via HACS

1. In HACS, go to **Integrations** and click the three-dot menu → **Custom repositories**
2. Add this repository URL and select category **Integration**
3. Install **Freezer Inventory**
4. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Freezer Inventory**
3. Select your todo list from the dropdown

## Todo list format

Each item in your todo list should be set up as follows:

| Field | Usage |
|---|---|
| **Title** | Name of the item (e.g. *Chicken breast*) |
| **Description** | Number of portions as an integer (e.g. `3`) |
| **Due date** | Expiration date |

Items without a numeric description are ignored.

## Lovelace card

After setup, add the card to your dashboard:

```yaml
type: custom:freezer-inventory-card
entity: sensor.freezer_inventory
title: Freezer
```

`title` is optional. Tapping a tile decrements its portion count by one.

## Service: `freezer_inventory.freezer_minus`

Decrements the portion count of an item by one.

| Field | Description |
|---|---|
| `item` | Item name (title in the todo list) |
| `portions` | Current portion count |
