# 🥗 Fitapp

**Fitapp** is a sports nutrition and healthy lifestyle application designed to help users improve their nutrition, track their meals, manage their ingredients, discover recipes, and connect their nutrition with physical activity.

The application combines a **React Native / Expo mobile application**, a **FastAPI backend**, a **PostgreSQL database**, and **AI-powered features**.

---

## ✨ Features

### 🥗 Nutrition

- Personalized nutrition profile
- Daily calorie estimation
- Macronutrient targets
- Protein, carbohydrate and fat tracking
- Nutrition goals
- Weight management
- Muscle gain
- Fat loss
- Performance optimization
- Healthy lifestyle goals

### 🍽️ Meal Tracking

- Add meals
- Calculate meal calories and macronutrients
- Track daily nutrition
- Food database
- Food quantities and units
- Ingredient management
- Nutrition history

### 📷 AI Meal Photo Analysis

Fitapp can analyze a meal from a photo using an AI vision model.

The AI can identify:

- Foods present in the meal
- Estimated quantities
- Preparation type
- Confidence level

The detected foods are then matched with the Fitapp food database before calculating the nutritional values.

The production pipeline is:

```text
┌──────────────────────┐
│   Fitapp Mobile App  │
│   React Native/Expo  │
└──────────┬───────────┘
           │
           │ Meal Photo
           ▼
┌──────────────────────┐
│      FastAPI         │
│      Backend         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Hugging Face        │
│  ZeroGPU             │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Qwen2.5-VL-3B        │
│ Instruct              │
└──────────┬───────────┘
           │
           │ Detected foods
           ▼
┌──────────────────────┐
│   Food Matching      │
│      Service         │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Fitapp Food DB     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Nutrition Calculator │
└──────────────────────┘
```

The AI is responsible for visual food identification and estimation.

The final nutritional calculation is performed by the Fitapp backend using the application's food database.

🤖 AI Assistant

Fitapp also includes an AI assistant.

The assistant can help users with:

Questions about Fitapp
Nutrition questions
Meal-related questions
Food information
Daily nutrition
User goals
Inventory
Recipes
Training
General questions

The AI assistant communicates with the application through the FastAPI backend rather than accessing the database directly.

🏋️ Training & Sports

Fitapp is designed for different types of users, including:

Beginners
Amateur athletes
Semi-professional athletes
Professional athletes
Users who simply want a healthier lifestyle

Supported sports and activities include:

⚽ Football
🏋️ Strength training
🏃 Running
🚴 Cycling
🥊 Combat sports
🏊 Swimming
Other activities

The application can take physical activity and user goals into account when calculating nutritional targets.

💧 Hydration

Fitapp includes hydration tracking to help users monitor their daily water intake.

🛒 Inventory

Users can manage available ingredients and foods.

The inventory can be used to:

Track available ingredients
Find foods already available
Generate meal ideas
Help with recipe suggestions
📖 Recipes

Fitapp provides recipe-related features to help users find ideas based on:

Available ingredients
Nutrition goals
Food preferences
Meal requirements
🌍 Multilingual Support

Fitapp supports multiple languages:

🇫🇷 French
🇬🇧 English
🇩🇿 Arabic
🇪🇸 Spanish

The backend includes a localization system for translations and multilingual application data.

🏗️ Tech Stack
📱 Frontend
React Native
Expo
Expo Router
JavaScript
React
react-native-safe-area-context
Expo Fonts
⚙️ Backend
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
Uvicorn
HTTPX
Pillow
Pillow HEIF
🗄️ Database
PostgreSQL
Neon PostgreSQL
SQLAlchemy ORM
Alembic migrations
🧠 Artificial Intelligence
Meal Vision
Hugging Face
ZeroGPU
Qwen2.5-VL-3B-Instruct
Gradio Client
PyTorch
Transformers
AI Assistant
Kie AI
FastAPI AI service layer
☁️ Deployment

The backend is designed to run on:

Render

The database is hosted using:

Neon PostgreSQL

The meal vision service runs through:

Hugging Face ZeroGPU

Production architecture:

                   ┌──────────────────────┐
                   │    Fitapp Mobile     │
                   │   React Native/Expo  │
                   └──────────┬───────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │       Render         │
                   │      FastAPI         │
                   └───────┬───────┬──────┘
                           │       │
                ┌──────────┘       └──────────┐
                ▼                             ▼
       ┌────────────────┐            ┌──────────────────┐
       │ Neon PostgreSQL│            │ Hugging Face     │
       │   Database     │            │     ZeroGPU      │
       └────────────────┘            └────────┬─────────┘
                                              │
                                              ▼
                                     Qwen2.5-VL-3B
📁 Project Structure
Fitapp/
│
├── backend/
│   │
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── i18n/
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── scripts/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── .env.example
│   └── .python-version
│
├── frontend/
│   │
│   ├── app/
│   ├── screens/
│   ├── components/
│   ├── assets/
│   ├── package.json
│   └── ...
│
├── README.md
└── LICENSE
🚀 Backend Installation
1. Clone the repository
git clone https://github.com/mohammedibra225-stack/Fitapp.git

Enter the project:

cd Fitapp
2. Go to the backend
cd backend
3. Create a virtual environment
Windows
python -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1
4. Install dependencies
pip install -r requirements.txt
5. Configure environment variables

Create a .env file based on:

.env.example

Example configuration:

API_HOST=0.0.0.0
API_PORT=8000

DEFAULT_LANGUAGE=fr

DATABASE_URL=your_postgresql_database_url

SPOONACULAR_API_KEY=your_spoonacular_api_key

KIE_API_KEY=your_kie_api_key

Never commit your real .env file or API keys to GitHub.

6. Run database migrations
alembic upgrade head
7. Start the backend
uvicorn app.main:app --reload

The API will normally be available at:

http://127.0.0.1:8000
📚 API Documentation

When the backend is running, FastAPI automatically provides Swagger documentation.

Open:

http://127.0.0.1:8000/docs

Alternative documentation:

http://127.0.0.1:8000/redoc
📱 Frontend Installation

Go to the frontend directory:

cd frontend

Install dependencies:

npm install

Start Expo:

npx expo start

You can then run the application using:

Android emulator
Physical Android device
Expo development tools
🔌 API Configuration

The mobile application communicates with the FastAPI backend.

Configure the API base URL according to the environment.

Example:

export const API_BASE_URL = 'https://your-api-url.com';

For local development, the URL depends on the device/emulator configuration.

🧮 Nutrition Calculation

Fitapp uses the user's profile information to calculate nutritional requirements.

The system can take into account:

Age
Sex
Height
Weight
Activity level
Sport
Goal

Possible goals include:

Eat healthier
Build muscle
Lose fat
Maintain weight
Improve performance
Healthy lifestyle

The backend then calculates nutritional targets such as:

Daily calories
Protein
Carbohydrates
Fat

Meal calculations are performed using the application's food database.

🍎 Food Database

Fitapp contains a structured food database with nutritional information.

Food records can include:

Name
Slug
Calories
Protein
Carbohydrates
Fat
Serving information
Unit
Price information
Translations

The backend also includes food matching to connect AI-detected food names with foods stored in the database.

🔍 AI Food Matching

The meal-analysis system does not directly trust the name returned by the vision model.

Instead:

AI detected food
       │
       ▼
Normalization
       │
       ▼
Alias matching
       │
       ▼
Exact matching
       │
       ▼
Fuzzy matching
       │
       ▼
Fitapp Food

This allows different names and languages to be mapped to the same food.

For example:

pommes de terre
pommes de terre frites
patates

can be matched to the appropriate food record.

🔐 Security

Do not commit sensitive information.

The following must remain private:

.env
DATABASE_URL
API keys
AI API keys
Authentication credentials
Private tokens

The project uses .gitignore to prevent local environment files and other sensitive development files from being committed.

🧪 Development

Before submitting changes, it is recommended to:

Test the backend.
Test database migrations.
Test affected API endpoints.
Test the mobile screens.
Test AI features when modified.
Verify that no secrets are included.
Review Git changes before pushing.

Check Git status:

git status

Review changes:

git diff
🤝 Contributing

Contributions, suggestions, bug reports and improvements are welcome.

To contribute:

Fork the repository.
Create a new branch.
Make your changes.
Test your changes.
Commit your changes.
Push the branch.
Open a Pull Request.

Example:

git checkout -b feature/my-feature
git add .
git commit -m "Add my feature"
git push origin feature/my-feature
📌 Project Status

Fitapp is an actively developed project.

Current development includes:

Mobile application
FastAPI backend
PostgreSQL database
Nutrition system
Food database
Meal tracking
AI meal photo analysis
AI assistant
Inventory
Recipes
Training
Hydration
Notifications
Multilingual support
Production deployment

Some features may still be under development or subject to change.

🗺️ Roadmap

Future development may include:

 Improved AI meal recognition
 More food database entries
 Improved nutrition recommendations
 Advanced training integration
 More recipe recommendations
 Improved meal planning
 More detailed progress tracking
 Additional languages
 Android production release
 Further AI assistant improvements
 Performance and UX improvements
👨‍💻 Author

Mohammed Ibrahim Benabdallah

Automatic Engineering / Automation

GitHub:

https://github.com/mohammedibra225-stack

📄 License

Fitapp is released under the MIT License.

See the LICENSE file for more information.

⭐ Support

If you find the project interesting, you can:

⭐ Star the repository
🐛 Report bugs
💡 Suggest improvements
🔧 Contribute to the project

Fitapp — Nutrition, Training & Healthy Lifestyle. 🥗🏋️📱
