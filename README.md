# Rust VIP Sales - Pterodactyl Egg

A modern Flask application for managing VIP package sales for Rust servers. This application provides a beautiful, Rust-themed interface for players to purchase VIP packages using cryptocurrency payments.

## Features

- 🎮 Modern, Rust-themed UI design
- 👤 User authentication system
- 🛒 Multiple VIP package options
- 💳 Cryptocurrency payment integration
- 🎮 Steam ID verification
- 📊 Real-time player count display
- 👑 Admin panel for order management
- ⚙️ Configurable settings through environment variables

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in a `.env` file:
   ```
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///app.db
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-password
   CRYPTO_ADDRESS=your-crypto-wallet-address
   STEAM_API_KEY=your-steam-api-key
   ```

5. Initialize the database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Run the application:
   ```bash
   python start.py
   ```

## Environment Variables

- `SECRET_KEY`: Flask secret key for session security
- `DATABASE_URL`: Database connection URL (defaults to SQLite)
- `ADMIN_USERNAME`: Username for admin panel access
- `ADMIN_PASSWORD`: Password for admin panel access
- `CRYPTO_ADDRESS`: Your cryptocurrency wallet address for payments
- `STEAM_API_KEY`: Your Steam API key for validating Steam IDs

## Admin Panel

Access the admin panel at `/admin` using your configured admin credentials. The admin panel allows you to:

- View and manage orders
- Update order statuses
- Configure payment settings
- Monitor sales statistics

## Security Notes

1. Always use strong passwords for admin access
2. Keep your `.env` file secure and never commit it to version control
3. Regularly update your cryptocurrency wallet address
4. Monitor transactions for payment verification

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
