# 🚗 FindMySpot - Vehicle Parking Management System

FindMySpot is a full-stack web application designed to simplify parking management for both administrators and users. The system allows users to search for parking lots, book available spots, and track their booking history. Admins can manage lots, monitor user activity, and keep the system updated.

---

## 📑 Features

### 👥 User Panel
- ✅ User Registration & Login
- 🔍 Search Parking Lots (by name, address, city, or pincode)
- 📅 Real-Time Spot Booking
- ⏱ Duration Tracking & Cost Calculation
- 📊 Booking History & Summary

### 🛠 Admin Panel
- 👨‍💼 Admin Login
- 🗂 Add / Edit Parking Lots
- 🧮 Auto-Manage Parking Spots (based on max capacity)
- 🔎 Search Users and Parking Lots
- 📈 View User Booking History

---

## 🧰 Tech Stack

| Layer          | Technology                      |
|----------------|----------------------------------|
| Backend        | Flask (Python)                  |
| ORM/Database   | SQLAlchemy + SQLite             |
| Frontend       | HTML, Bootstrap 5, Jinja2       |
| Authentication | Flask-Login                     |

---

## 🗃 Database Models

### 🧑‍💼 User & Admin
- `Admin`: Manages parking system
- `User`: Registers & books parking

### 🅿 Parking Structure
- `ParkingLot`: Lot details (name, address, capacity)
- `ParkingSpot`: Individual parking spot, status tracked (A = Available, O = Occupied)
- `ReservedParkingSpot`: Booking history with timestamps, vehicle number, cost, etc.

---
