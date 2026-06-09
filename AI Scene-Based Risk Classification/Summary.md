The code idea is to build an AI-based safety risk classifier that looks at an image and decides whether the scene is SAFE or RISKY.

The system does not depend on only one model. It combines three models:

YOLOv8 – detects objects in the image
Example: fire, smoke, gun, person, helmet, safety gear.
ResNet50 – understands the scene/context
Example: whether the image is indoor, outdoor, worksite, kitchen, road, park, etc.
MobileNetV3 – classifies the overall risk level
It checks whether the image pattern looks safe or dangerous.

The main idea is:
An object alone does not always decide risk. The surrounding scene also matters.

For example, a person without a helmet may not be risky in a park, but it is risky in a construction site. Similarly, fog may look like smoke, so the system tries to use multiple clues before deciding.

The code uses a voting or ensemble logic. That means each model gives its own signal, and the final output is decided by combining them. The system is designed to be cautious: it may sometimes mark a safe image as risky, but it tries to avoid missing real dangers like fire, explosion, smoke, or unsafe workplace conditions.

In simple words:

The code tries to make a computer “look at a scene like a safety inspector” by detecting objects, understanding the environment, and then deciding whether the situation is safe or risky.

The project tested this idea on workplace safety images and disaster images. It achieved about 76.5% accuracy on worksite PPE/helmet-related images and about 63% accuracy on unseen disaster images after adding the voting logic.
