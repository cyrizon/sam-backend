# sam-backend

This project serves as the backend for the **SAM** application, a route optimization solution. The backend is written in Python using the Flask framework and interacts with a self-hosted **OpenRouteService** instance to generate and optimize routes.

## Objectives

This repository aims to:
- Provide a RESTful API for the **SAM** frontend to request route optimizations and other functionalities.
- Handle user data and business logic related to route planning.
- Act as a bridge between the **SAM** frontend and the self-hosted **OpenRouteService** (ORS).

## How It Works

1. **Frontend Interaction**: The **SAM** frontend sends requests (e.g., coordinates) to the backend via RESTful API endpoints.
2. **Backend Processing**: The backend processes the request and forwards it to the self-hosted **OpenRouteService** instance.
3. **ORS Communication**: The self-hosted ORS instance (typically written in Java) performs the heavy lifting of route calculation and optimization.
4. **Response Delivery**: The backend receives the optimized route from ORS and returns it to the frontend for display and further processing.

## Features

- **RESTful API**: Provides endpoints for frontend interaction, including route requests and user-related operations.
- **Integration with OpenRouteService**: Communicates with a Java-based self-hosted **OpenRouteService** instance to generate optimized routes.
- **Data Management**: Handles and validates input data from the frontend before forwarding it to ORS.
- **Scalable Design**: Ensures that the backend can handle multiple requests efficiently.

## Getting Started

To get started with this project, follow these steps:

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/cyrizon/sam-backend.git
   ```

2. **Install Dependencies**:
   Make sure you have Python 3.8+ installed. Then, install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. **Run the Backend**:
   Start the Flask development server:
   ```sh
   flask run
   ```

## Environment Variables

The backend uses the following environment variables for configuration:
- `ORS_API_URL`: The URL of your self-hosted **OpenRouteService** instance.
- `ORS_API_KEY`: The API key required to authenticate with the ORS instance.
