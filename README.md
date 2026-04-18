# 🔄 Procure-to-Pay (P2P) — SAP MM End-to-End Implementation

> **Capstone Project | KIIT University | Swaraj Kumar Behera**

A complete, industry-standard **Procure-to-Pay (P2P)** process implementation using **SAP Materials Management (MM)** for a fictitious manufacturing company — **NovaTrade Pvt. Ltd.**

---

## 🏢 Company Overview

| Field | Value |
|---|---|
| Company | NovaTrade Pvt. Ltd. |
| Company Code | NOVT |
| Plant | NO01 — Bhubaneswar Manufacturing Plant |
| Storage Location | SL01 — Main Warehouse |
| Purchase Organization | NOPO — Central Purchase Org. |
| Purchase Group | N01 — General Procurement Team |

---

## 🔁 P2P Process Flow

```
Purchase Requisition (PR)
        ↓
Request for Quotation (RFQ)
        ↓
Vendor Quotation Entry
        ↓
Price Comparison & Vendor Selection
        ↓
Purchase Order (PO)
        ↓
Goods Receipt (GR)
        ↓
Invoice Verification (3-Way Match)
        ↓
Vendor Payment
```

---

## 📋 Step-by-Step Process

### Step 1 — Purchase Requisition `ME51N`
- Raised by the stores department for **500 units of RM-STEEL-001 (Steel Rods)**
- Specifies: material, quantity, required delivery date, plant

### Step 2 — Request for Quotation `ME41`
- RFQ sent to 3 approved vendors (V001, V002, V003)
- Requests: unit price, lead time, payment terms

### Step 3 — Enter Vendor Quotations `ME47`
- Vendor responses entered into SAP against each RFQ

### Step 4 — Price Comparison & Selection `ME49`
- SAP generates a comparison report
- **V001 (RawMat Suppliers India Ltd.)** selected — ₹850/unit, 7-day lead time

### Step 5 — Purchase Order `ME21N`
- PO raised for 500 units @ ₹850 = **Total ₹4,25,000**
- Released and dispatched to vendor

### Step 6 — Goods Receipt `MIGO (MVT 101)`
- 500 units physically verified and received
- Stock automatically updated in SL01

### Step 7 — Invoice Verification `MIRO`
- Vendor invoice for ₹4,25,000 processed
- Automatic **3-Way Match**: PO ✅ + GR ✅ + Invoice ✅

### Step 8 — Vendor Payment `F110`
- Automatic payment run executed
- ₹4,25,000 transferred to V001's bank account

---

## 🛠️ Tech Stack

| Component | Details |
|---|---|
| ERP Platform | SAP ECC 6.0 / SAP S/4HANA |
| Module | SAP MM (Materials Management) |
| Integrated Modules | SAP FI (Finance) |
| Key T-Codes | ME51N, ME41, ME47, ME49, ME21N, MIGO, MIRO, F110 |
| Master Data | Vendor Master, Material Master, Purchasing Info Records |

---

## ✨ Unique Points

- **Real-world Indian manufacturing scenario** with actual material codes and plant structures
- **3-Way Match** invoice verification — a critical financial control mechanism
- **Cross-module integration** — MM + FI from procurement to payment
- **Complete T-Code documentation** — usable as a training guide
- **Competitive vendor evaluation** via price comparison (ME49)

---

## 🚀 Future Improvements

- Contract Management (`ME31K`) for recurring procurement
- Vendor Portal via SAP SRM for digital invoice submission
- Multi-level PR Approval Workflow using SAP Business Workflow
- Spend Analytics Dashboard via SAP Analytics Cloud
- Batch Management for quality/recall traceability
- EDI Integration for automated PO dispatch

---

## 📁 Repository Structure

```
📦 sap-p2p-implementation/
 ┣ 📄 README.md                     ← This file
 ┣ 📄 SAP_P2P_Project_Documentation.pdf  ← Full project report (submit this)
 ┣ 📂 screenshots/
 ┃ ┣ 01_ME51N_Purchase_Requisition.png
 ┃ ┣ 02_ME41_RFQ_Creation.png
 ┃ ┣ 03_ME47_Quotation_Entry.png
 ┃ ┣ 04_ME49_Price_Comparison.png
 ┃ ┣ 05_ME21N_Purchase_Order.png
 ┃ ┣ 06_MIGO_Goods_Receipt.png
 ┃ ┣ 07_MIRO_Invoice_Verification.png
 ┃ ┗ 08_F110_Payment_Run.png
 ┗ 📄 NovaTrade_Company_Config.md   ← Org structure config details
```

---

## 👤 Author

**Swaraj Kumar Behera**  
B.Tech CSE | KIIT University, Bhubaneswar  
Roll Number: 23053092 | Batch/Program: 2023-2027 / B.Tech CSE  
GitHub: [github.com/swaraj3092](https://github.com/swaraj3092)

---

> *Submitted as part of the Capstone Project — April 2026*
