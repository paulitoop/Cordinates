import numpy as np
import tkinter as tk
from tkinter import filedialog
import pyproj
import os
import re
from PIL import Image, ImageTk

def rot_euler(theta): #определение матрциы поворота
    phi, theta, psi = theta
    R_x = np.array([[1, 0, 0], [0, np.cos(phi), -np.sin(phi)], [0, np.sin(phi), np.cos(phi)]])
    R_y = np.array([[np.cos(theta), 0, np.sin(theta)], [0, 1, 0], [-np.sin(theta), 0, np.cos(theta)]])
    R_z = np.array([[np.cos(psi), -np.sin(psi), 0], [np.sin(psi), np.cos(psi), 0], [0, 0, 1]])
    return np.dot(np.dot(R_x,R_y),R_z )

class Camera:
    def __init__(self, w, h, f_x, f_y, cent_x, cent_y,cam_x, cam_y, cam_z, rot_x, rot_y, rot_z ):
        self.w = w
        self.h = h
        self.f_x = f_x
        self.f_y = f_y
        self.cent_x = cent_x
        self.cent_y = cent_y
        self.cam_x = cam_x
        self.cam_y = cam_y
        self.cam_z = cam_z
        self.rot_x = rot_x
        self.rot_y = rot_y
        self.rot_z = rot_z

    def pix_to_cord(self, x_pix, y_pix):#определение координат по пикселю
        SizeY = self.h
        dist = self.cam_z

        R = rot_euler([np.radians(self.rot_x), np.radians(self.rot_y), np.radians(self.rot_z)]) #созадние матрицы поворота
        Rtr = np.transpose(R)
        trans1 = pyproj.Transformer.from_crs(4326, 3857) #созадние трансформера для перевода WGS84 в Меркатора
        trans2 = pyproj.Transformer.from_crs(3857, 4326) #создание трансформера для перевода Меркатора в WGS84

        value1 = trans1.transform(self.cam_x, self.cam_y) #перевод широты и долготы в проекцию Меркатора (x и y)
        cam_x = value1[0]
        cam_y = value1[1]
        t = np.array([[cam_x], [cam_y], [-self.cam_z]]) #вектор трансляции камеры

        xy = np.array([[x_pix], [y_pix], [1]])
        xy[1] = SizeY - xy[1]
        xy *= int(dist)

        A = np.array([[self.f_x, 0, self.cent_x], #матрица внутренних параметров камеры
                      [0, self.f_y, self.cent_y],
                      [0, 0, 1]])

        Ainv = np.linalg.inv(A)
        Rtr_t = Rtr@t
        Ainv_xy = Ainv @ xy
        Rtr_t_Ainv_xy = Rtr_t +  Ainv_xy
        XYZ = R@Rtr_t_Ainv_xy

        value2 = trans2.transform(XYZ[0], XYZ[1]) #обратный перевод в систему WGS84

        return value2

def read_camera_parameters(filename, image_name): #функция подгрузки конфигурации камеры из файла config.txt
    with open(filename, 'r') as file:
        lines = file.readlines()

        # Ищем строку, содержащую имя файла
        for line in lines:
            if re.search(r'\b{}\b'.format(re.escape(image_name)), line):
                parameters = line.split()[1:]
                return parameters

    return None
root = tk.Tk()
root.title("Image Viewer")

# Выбор изображения
file_path = tk.filedialog.askopenfilename()
if file_path == "":
    root.destroy()
    exit()

# Открытие выбранного изображения
image = Image.open(file_path)
file_name = os.path.basename(file_path)

# Считываем параметры и создаем на их основе класс
parametrs = read_camera_parameters('config.txt', file_name)
parametrs.pop(0)
Camera_google = Camera(int(parametrs[0]), int(parametrs[1]), int(parametrs[2]), int(parametrs[3]), int(parametrs[4]), \
                       int(parametrs[5]), float(parametrs[6]), float(parametrs[7]), \
                       float(parametrs[8]), float(parametrs[9]), float(parametrs[10]), float(parametrs[11]))

new_res = (int(parametrs[0]), int(parametrs[1]))
image = image.resize(new_res)
photo = ImageTk.PhotoImage(image)
canvas = tk.Canvas(root, width=image.width, height=image.height)
canvas.pack()
canvas.create_image(0, 0, anchor="nw", image=photo)

# Создаем список для хранения точек
points = []

# Функция для добавления точки на изображение
def add_point(x, y):
    red_dot = canvas.create_oval(x+5, y+5, x -5, y -5, fill="red")
    points.append(red_dot)

# Функция для удаления предыдущей точки
def remove_last_point():
    if points:
        last_point = points.pop()
        canvas.delete(last_point)

# Присваиваем макрос нажатию кнопки мыши
def on_click(event):
    print("Mouse clicked at x =", event.x, "y =", event.y)
    mas = Camera_google.pix_to_cord(event.x, event.y)
    print(f"Obj cords at lat, long = {(mas[0][0]), (mas[1][0])}")

    remove_last_point()  # Удаляем предыдущую точку
    add_point(event.x, event.y)  # Добавляем новую точку

canvas.bind("<Button-1>", on_click)
root.mainloop()