import sys
from face_detection import FaceAlignment,LandmarksType
from os import listdir, path
import subprocess
import numpy as np
import cv2
import pickle
import os
import json
from typing import Optional, Tuple
# from mmpose.apis import inference_topdown, init_model
# from mmpose.structures import merge_data_samples
try:
    import mediapipe as mp
except ImportError:  # pragma: no cover
    mp = None

import torch
from tqdm import tqdm

# initialize the mmpose model
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# config_file = './avatars/musetalk/utils/dwpose/rtmpose-l_8xb32-270e_coco-ubody-wholebody-384x288.py'
# checkpoint_file = './models/dwpose/dw-ll_ucoco_384.pth'
# model = init_model(config_file, checkpoint_file, device=device)

# initialize the face detection model
device = "cuda" if torch.cuda.is_available() else "cpu"
fa = FaceAlignment(LandmarksType._2D, flip_input=False,device=device)

# maker if the bbox is not sufficient 
coord_placeholder = (0.0,0.0,0.0,0.0)

_MP_FACE_MESH = None
_MP_LANDMARK_NOSE_CENTER = 168
_MP_LANDMARK_FOREHEAD = 10
_MP_LANDMARK_CHIN = 152
_MP_FACE_OUTLINE_COUNT = 468
_HALF_FACE_DIST_SCALE = 0.90


def _get_mediapipe_face_mesh():
    global _MP_FACE_MESH
    if _MP_FACE_MESH is not None:
        return _MP_FACE_MESH
    if mp is None:
        raise ModuleNotFoundError(
            "mediapipe is required for musetalk preprocessing. "
            "Install it with `pip install mediapipe`."
        )
    _MP_FACE_MESH = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.5,
    )
    return _MP_FACE_MESH


def _crop_rgb(img_rgb: np.ndarray, roi: Tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = roi
    return img_rgb[y1:y2, x1:x2]


def _mediapipe_face_landmarks_xy(
    img_rgb: np.ndarray,
    *,
    roi: Optional[Tuple[int, int, int, int]] = None,
) -> Optional[np.ndarray]:
    """Return face mesh landmarks as (N,2) pixel coords, or None if no face.

    If roi is provided, run FaceMesh on the cropped region and map points back to full coords.
    """
    if roi is None:
        rgb = img_rgb
        offset_x = 0
        offset_y = 0
    else:
        x1, y1, x2, y2 = roi
        if x2 <= x1 or y2 <= y1:
            return None
        rgb = _crop_rgb(img_rgb, roi)
        offset_x = x1
        offset_y = y1

    mesh = _get_mediapipe_face_mesh()
    results = mesh.process(rgb)
    if not results.multi_face_landmarks:
        return None
    face = results.multi_face_landmarks[0]
    h, w = rgb.shape[:2]
    pts = np.array([(lm.x * w + offset_x, lm.y * h + offset_y) for lm in face.landmark], dtype=np.float32)
    return np.round(pts).astype(np.int32)

def resize_landmark(landmark, w, h, new_w, new_h):
    w_ratio = new_w / w
    h_ratio = new_h / h
    landmark_norm = landmark / [w, h]
    landmark_resized = landmark_norm * [new_w, new_h]
    return landmark_resized

def read_imgs(img_list):
    frames = []
    print('reading images...')
    for img_path in tqdm(img_list):
        frame = cv2.imread(img_path)
        frames.append(frame)
    return frames

# def get_bbox_range(img_list,upperbondrange =0):
#     frames = read_imgs(img_list)
#     batch_size_fa = 1
#     batches = [frames[i:i + batch_size_fa] for i in range(0, len(frames), batch_size_fa)]
#     coords_list = []
#     landmarks = []
#     if upperbondrange != 0:
#         print('get key_landmark and face bounding boxes with the bbox_shift:',upperbondrange)
#     else:
#         print('get key_landmark and face bounding boxes with the default value')
#     average_range_minus = []
#     average_range_plus = []
#     for fb in tqdm(batches):
#         results = inference_topdown(model, np.asarray(fb)[0])
#         results = merge_data_samples(results)
#         keypoints = results.pred_instances.keypoints
#         face_land_mark= keypoints[0][23:91]
#         face_land_mark = face_land_mark.astype(np.int32)
        
#         # get bounding boxes by face detetion
#         bbox = fa.get_detections_for_batch(np.asarray(fb))
        
#         # adjust the bounding box refer to landmark
#         # Add the bounding box to a tuple and append it to the coordinates list
#         for j, f in enumerate(bbox):
#             if f is None: # no face in the image
#                 coords_list += [coord_placeholder]
#                 continue
            
#             half_face_coord =  face_land_mark[29]#np.mean([face_land_mark[28], face_land_mark[29]], axis=0)
#             range_minus = (face_land_mark[30]- face_land_mark[29])[1]
#             range_plus = (face_land_mark[29]- face_land_mark[28])[1]
#             average_range_minus.append(range_minus)
#             average_range_plus.append(range_plus)
#             if upperbondrange != 0:
#                 half_face_coord[1] = upperbondrange+half_face_coord[1] #手动调整  + 向下（偏29）  - 向上（偏28）

#     text_range=f"Total frame:「{len(frames)}」 Manually adjust range : [ -{int(sum(average_range_minus) / len(average_range_minus))}~{int(sum(average_range_plus) / len(average_range_plus))} ] , the current value: {upperbondrange}"
#     return text_range
    

def get_landmark_and_bbox(img_list,upperbondrange =0):
    frames = read_imgs(img_list)
    batch_size_fa = 1
    batches = [frames[i:i + batch_size_fa] for i in range(0, len(frames), batch_size_fa)]
    coords_list = []
    landmarks = []
    if upperbondrange != 0:
        print('get key_landmark and face bounding boxes with the bbox_shift:',upperbondrange)
    else:
        print('get key_landmark and face bounding boxes with the default value')
    average_range_minus = []
    average_range_plus = []
    for fb in tqdm(batches):
        # results = inference_topdown(model, np.asarray(fb)[0])
        # results = merge_data_samples(results)
        # keypoints = results.pred_instances.keypoints
        # face_land_mark= keypoints[0][23:91]
        # face_land_mark = face_land_mark.astype(np.int32)
        img_rgb = cv2.cvtColor(np.asarray(fb)[0], cv2.COLOR_BGR2RGB)
        
        # get bounding boxes by face detetion
        bbox = fa.get_detections_for_batch(np.asarray(fb))
        
        # adjust the bounding box refer to landmark
        # Add the bounding box to a tuple and append it to the coordinates list
        for j, f in enumerate(bbox):
            if f is None: # no face in the image
                coords_list += [coord_placeholder]
                continue

            x1_f, y1_f, x2_f, y2_f = map(int, f)
            roi = (max(0, x1_f), max(0, y1_f), max(0, x2_f), max(0, y2_f))
            mesh_pts = _mediapipe_face_landmarks_xy(img_rgb, roi=roi)
            if mesh_pts is None:
                coords_list += [f]
                average_range_minus.append(0)
                average_range_plus.append(0)
                continue

            outline = mesh_pts[:_MP_FACE_OUTLINE_COUNT] if len(mesh_pts) >= _MP_FACE_OUTLINE_COUNT else mesh_pts
            min_x = int(np.min(outline[:, 0]))
            max_x = int(np.max(outline[:, 0]))
            max_y = int(np.max(outline[:, 1]))

            if _MP_LANDMARK_NOSE_CENTER < len(mesh_pts):
                half_face_coord = mesh_pts[_MP_LANDMARK_NOSE_CENTER].copy()
            else:
                half_face_coord = np.array([int((min_x + max_x) / 2), int(max_y / 2)], dtype=np.int32)

            if _MP_LANDMARK_FOREHEAD < len(mesh_pts) and _MP_LANDMARK_CHIN < len(mesh_pts):
                range_minus = half_face_coord[1] - mesh_pts[_MP_LANDMARK_FOREHEAD][1]
                range_plus = mesh_pts[_MP_LANDMARK_CHIN][1] - half_face_coord[1]
            else:
                range_minus = 0
                range_plus = 0

            average_range_minus.append(int(range_minus))
            average_range_plus.append(int(range_plus))

            if upperbondrange != 0:
                half_face_coord[1] = upperbondrange + half_face_coord[1] #手动调整  + 向下（偏29）  - 向上（偏28）

            half_face_dist = int((max_y - half_face_coord[1]) * _HALF_FACE_DIST_SCALE)
            min_upper_bond = 0
            upper_bond = max(min_upper_bond, half_face_coord[1] - half_face_dist)
            
            f_landmark = (min_x, int(upper_bond), max_x, max_y)
            x1, y1, x2, y2 = f_landmark
            
            if y2-y1<=0 or x2-x1<=0 or x1<0: # if the landmark bbox is not suitable, reuse the bbox
                coords_list += [f]
                w,h = f[2]-f[0], f[3]-f[1]
                print("error bbox:",f)
            else:
                coords_list += [f_landmark]
    
    print("********************************************bbox_shift parameter adjustment**********************************************************")
    minus_avg = int(sum(average_range_minus) / len(average_range_minus)) if average_range_minus else 0
    plus_avg = int(sum(average_range_plus) / len(average_range_plus)) if average_range_plus else 0
    print(f"Total frame:「{len(frames)}」 Manually adjust range : [ -{minus_avg}~{plus_avg} ] , the current value: {upperbondrange}")
    print("*************************************************************************************************************************************")
    return coords_list,frames
    

if __name__ == "__main__":
    img_list = ["./results/lyria/00000.png","./results/lyria/00001.png","./results/lyria/00002.png","./results/lyria/00003.png"]
    crop_coord_path = "./coord_face.pkl"
    coords_list,full_frames = get_landmark_and_bbox(img_list)
    with open(crop_coord_path, 'wb') as f:
        pickle.dump(coords_list, f)
        
    for bbox, frame in zip(coords_list,full_frames):
        if bbox == coord_placeholder:
            continue
        x1, y1, x2, y2 = bbox
        crop_frame = frame[y1:y2, x1:x2]
        print('Cropped shape', crop_frame.shape)
        
        #cv2.imwrite(path.join(save_dir, '{}.png'.format(i)),full_frames[i][0][y1:y2, x1:x2])
    print(coords_list)
