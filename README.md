# Airport API Service

## Overview

This is a RESTful API service for an airport management system built with
Django REST Framework. The API allows users to browse flights, make bookings,
and manage user accounts.

## Features

- JWT-based authentication system
- Dedicated admin panel at /admin/
- Documentation with Swagger
- Managing orders and tickets
- Creating and managing flights, airlines, airports, routes, and more
- Countries and Cities
- Airports and Routes
- Airlines and Airplanes
- Crew members and roles
- Seat classes and compartments
- Filter flights by airline, route, source, destination, departure date, and
  arrival date

## Installation and Setup

### Prerequisites

- Docker and Docker Compose installed on your system
- Git for cloning the repository

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/tetianasobko/airport-api-service.git
   cd airport-api-service
   ```

2. **Set up environment variables**
   Create a `.env` file in the root directory based on the provided
   `.env.example`:
   ```
   POSTGRES_DB=your_db_name
   POSTGRES_USER=your_db_user
   POSTGRES_PASSWORD=your_db_password
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   PGDATA=/var/lib/postgresql/data
   ```

3. **Build and run the Docker containers**
   ```bash
   docker-compose up --build
   ```
   This will:
    - Build the Docker image for the application
    - Start the PostgreSQL database
    - Run database migrations
    - Start the Django development server

4. **Access the API**
   The API will be available at: http://localhost:8000/

## API Documentation

The API documentation is available at:

- Swagger UI: http://localhost:8000/api/doc/swagger/

## Running Tests

To run the tests, execute the following command:

```bash
docker-compose run --rm app python manage.py test
```

## Development

For local development without Docker:

1. Create and activate a virtual environment
2. Install dependencies: `pip install -r requirements.txt`
3. Set up a local PostgreSQL database and update the `.env` file
4. Run migrations: `python manage.py migrate`
5. Start the development server: `python manage.py runserver`