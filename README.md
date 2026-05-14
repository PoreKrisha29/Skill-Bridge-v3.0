# 📚 SkillBridge V2.5

SkillBridge is a comprehensive, feature-rich service marketplace platform designed to seamlessly connect service providers (freelancers, professionals) with clients. It offers a secure, intuitive, and robust environment for managing services, orders, communications, and legal agreements.

## 🌟 Key Features

### 👥 User Management & Profiles
*   **Multi-Role System:** Supports Clients, Service Providers, and Administrators.
*   **Detailed Profiles:** Users can set up profiles with avatars, bios, and contact information.
*   **Google OAuth Integration:** Quick and secure login/registration using Google accounts.
*   **Provider Conversion:** Clients can seamlessly upgrade to become service providers when they create their first service.

### 🏪 Service Marketplace
*   **Advanced Browsing & Filtering:** Browse services by category, search by keywords, and filter by price range and rating.
*   **Service Listings:** Detailed service pages including descriptions, pricing, delivery times, images, and category tags.
*   **Smart Search:** Auto-detects categories based on search queries for better user experience.
*   **Favorites System:** Users can bookmark/favorite services for later viewing.

### 💼 Order & Transaction Management
*   **End-to-End Order Tracking:** Track orders through various states: Pending, In Progress, Completed, and Cancelled.
*   **Platform Fees:** Built-in calculation for platform commission fees.
*   **Delivery Management:** Secure handling of project requirements, scope, and final delivery notes.

### 📝 Legal-Grade Contracts
*   **Digital Signatures:** Secure, cryptographic hash-based digital signatures for both providers and clients.
*   **Comprehensive Agreements:** Includes terms for payment, revision policies, IP ownership, and cancellation policies.
*   **IP Tracking:** Records IP addresses and timestamps during the signing process for added security and compliance.

### ⭐ Reviews & Ratings
*   **Service Reviews:** Clients can leave 1-5 star ratings and detailed feedback on completed services.
*   **Rating Distributions:** Visual breakdown of ratings on service pages.
*   **Website Feedback:** Dedicated system for users to submit overall platform feedback and suggestions.

### 💬 Communication & Notifications
*   **Real-time Messaging:** Built-in chat system tied directly to specific orders for seamless provider-client communication.
*   **Notification System:** Alerts users about order updates, new messages, and platform announcements.

### 🎨 Project Showcase (Portfolios)
*   **Provider Portfolios:** Service providers can showcase their past work, including project titles, descriptions, images, and external links, directly on their profiles.

### 🤝 Communities
*   **User Groups:** Join active communities based on interests or professional domains.
*   **Member Tracking:** View community members and track membership status.

### 🛡️ Admin Dashboard
*   **Platform Moderation:** Administrators can manage users, oversee services, and moderate content.
*   **Data Deletion:** Admins have privileges for permanent data removal, whereas standard users utilize soft deletes.

## 🛠️ Technology Stack
*   **Backend:** Python, Flask
*   **Database:** SQLAlchemy (SQLite by default, easily upgradeable)
*   **Authentication:** Flask-Login, Werkzeug Security, Authlib (Google OAuth)
*   **Architecture:** MVC Pattern (Models, Views/Templates, Controllers/Routes)

## 🚀 Getting Started

1.  **Clone the repository.**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set up Environment Variables:**
    Copy `.env.example` to `.env` and fill in your configuration (Secret Keys, Database URI, Google OAuth credentials).
4.  **Initialize Database:**
    ```bash
    python init_db.py
    ```
5.  **Run the Application:**
    You can run the application using the provided batch file or manually:
    ```bash
    start.bat
    # OR
    python app.py
    ```

## 📄 Architecture Notes
The project is built with strong adherence to Object-Oriented Programming (OOP) and Database Management System (DBMS) concepts:
*   **Encapsulation:** Password hashing, internal status updates, and signature generation are securely encapsulated within models.
*   **Relationships:** Extensive use of One-to-Many and Many-to-Many relationships with appropriate foreign keys and cascading deletes.
*   **Optimization:** Strategic use of database indexes (including composite indexes) for faster querying.
