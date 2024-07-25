# GameBooker

GameBooker is a web application designed to streamline the reservation and management of gaming PCs in a LAN or gaming room. It features secure user authentication, real-time availability checks, a simple reservation system, dynamic password generation for each session, and an admin dashboard for PC management. With a responsive design and automated email notifications, GameBooker enhances the user experience and operational efficiency for gaming centers and cafes. Built with Flask (Python) and SQLite, it's easily scalable for larger deployments.

## Features

- Secure user authentication
- Real-time availability checks
- Simple reservation system
- Dynamic password generation
- Admin dashboard
- Responsive design
- Automated email notifications

## Technologies Used

- Frontend: HTML, CSS, JavaScript
- Backend: Flask (Python)
- Database: SQLite

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/GameBooker.git
    ```
2. Navigate to the project directory:
    ```bash
    cd GameBooker
    ```
3. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```
4. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
5. Run the application:
    ```bash
    python app.py
    ```

## Usage

1. Open your web browser and go to `http://127.0.0.1:5000/`.
2. Use the web interface to reserve PCs, check availability, and manage reservations.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.
