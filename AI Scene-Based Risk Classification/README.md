I have given two code files. Main.py is the main one and that should give you the accuracy of the model on unseen data. If you want to note the accuracy of the inner Work site safety model, which is a supplement model that tracks the people with helmets an safety kits, you can run the WorkSiteSafety.py where you can change the MODE variable to "train" and then test it by changing the variable to "test".

This project is designed to assess if an image depicts a "safe," "risky," or "very risky" scene. It uses three different models: YOLOv8 identifies objects like fire or helmets in the picture, ResNet determines if the scene is indoors or outdoors, and MobileNet models check for the presence of fire or if people are missing safety equipment. These models work together to evaluate the danger level of a scene. 

To begin, arrange your files and folders correctly. Place your images in specific folders: inside the FireDataset folder, have a train folder with two subfolders—one for "fire" and one for "non_fire." Do the same in the Worksite-Safety-Monitoring-Dataset/train folder. 

To train the model, change the MODE variable to MODE = "train", and wait for the model to run. It will choose the best models while it runs epochs and it will save it to best_models. T

For testing, set MODE to "evaluate" and run the code once more. This will look at all the images in a folder called Dataset_Created. Inside this folder, there should be two subfolders: one for safe_images and another for risky_images.

There are a lot of folders involved, so let me know if the program doesn't run well and I can show you the running process on my computer since the combination of data is complex.
