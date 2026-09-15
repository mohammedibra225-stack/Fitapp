from app.services.huggingface_vision_service import (
    huggingface_vision_service,
)


IMAGE_PATH = "test_meal.jpg"


result = huggingface_vision_service.analyze_meal(
    IMAGE_PATH
)

print("\n===== RESULTAT HUGGING FACE =====")
print(result)
print("=================================\n")