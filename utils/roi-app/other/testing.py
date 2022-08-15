import cv2
import numpy as np

# Create a zeros image
img = np.zeros((800,800), dtype=np.uint8)

# Specify the text location and rotation angle
text_location = (100,200)
angle = 0

# Draw the text using cv2.putText()
font = cv2.FONT_HERSHEY_SIMPLEX
cv2.putText(img, 'TheAILearner', text_location, font, 1, 255, 2)

# Rotate the image using cv2.warpAffine()
try:
    while True:
        angle += 1
        if angle > 360:
            angle = 0
        M = cv2.getRotationMatrix2D(text_location, angle, 1)
        out = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))

        cv2.imshow('img',out)
        cv2.waitKey(1)
except KeyboardInterrupt:
    cv2.destroyAllWindows()