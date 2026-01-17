import cv2
import mediapipe as mp

class YogaVisualizer:
    def __init__(self):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose
        
        self.line_style = self.mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2)
        self.point_style = self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=1)

    def draw_skeleton(self, frame, landmarks):
        if landmarks:
            self.mp_drawing.draw_landmarks(
                frame, 
                landmarks, 
                self.mp_pose.POSE_CONNECTIONS,
                self.point_style,
                self.line_style
            )
        return frame