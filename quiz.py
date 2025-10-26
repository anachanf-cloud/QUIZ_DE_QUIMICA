import cv2
import mediapipe as mp
import pygame
import time
import os

# === CONFIGURAÇÕES INICIAIS ===
pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Quiz Química - Armadillos")

# Caminhos das imagens
layers = {
    "START": r"C:\Projetos\Quiz_quimica\START.jpg",
    "PERGUNTA1": r"C:\Projetos\Quiz_quimica\PERGUNTA1.jpg",
    "RESPOSTA1": r"C:\Projetos\Quiz_quimica\RESPOSTA1.jpg",
    "PERGUNTA2": r"C:\Projetos\Quiz_quimica\PERGUNTA2.jpg",
    "RESPOSTA2": r"C:\Projetos\Quiz_quimica\RESPOSTA2.jpg",
    "PERGUNTA3": r"C:\Projetos\Quiz_quimica\PERGUNTA3.jpg",
    "RESPOSTA3": r"C:\Projetos\Quiz_quimica\RESPOSTA3.jpg",
    "PERGUNTA4": r"C:\Projetos\Quiz_quimica\PERGUNTA4.jpg",
    "RESPOSTA4": r"C:\Projetos\Quiz_quimica\RESPOSTA4.jpg",
    "PERGUNTA5": r"C:\Projetos\Quiz_quimica\PERGUNTA5.jpg",
    "RESPOSTA5": r"C:\Projetos\Quiz_quimica\RESPOSTA5.jpg",
    "PERGUNTA6": r"C:\Projetos\Quiz_quimica\PERGUNTA6.jpg",
    "RESPOSTA6": r"C:\Projetos\Quiz_quimica\RESPOSTA6.jpg",
    "CORRETO": r"C:\Projetos\Quiz_quimica\CORRETO.jpg",
    "INCORRETO": r"C:\Projetos\Quiz_quimica\INCORRETO.jpg"
}

# Tempos para gestos
TEMPO_CORRETO = 0.8  # segundos para reconhecer correto
TEMPO_INCORRETO = 3  # segundos para reconhecer incorreto

# === FUNÇÃO PARA CARREGAR IMAGENS COM VERIFICAÇÃO ===
def carregar_imagem(caminho):
    if not os.path.exists(caminho):
        print(f"[ERRO] Imagem não encontrada: {caminho}")
        return pygame.Surface((1280, 720))
    try:
        img = pygame.image.load(caminho)
        return pygame.transform.scale(img, (1280, 720))
    except Exception as e:
        print(f"[ERRO] Falha ao carregar imagem {caminho}: {e}")
        return pygame.Surface((1280, 720))

# === DETECÇÃO DE MÃO ===
mp_hands = mp.solutions.hands

def contar_dedos(hand_landmarks, hand_label):
    count = 0
    dedos_tipos = [8, 12, 16, 20]
    dedos_dobras = [6, 10, 14, 18]
    for tip, dob in zip(dedos_tipos, dedos_dobras):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[dob].y - 0.02:
            count += 1
    base_mao = hand_landmarks.landmark[0]
    ponta_polegar = hand_landmarks.landmark[4]
    if hand_label == "Right":
        if ponta_polegar.x < base_mao.x - 0.15:
            count += 1
    else:
        if ponta_polegar.x > base_mao.x + 0.05:
            count += 1
    return count

# === INICIALIZAÇÃO DA CÂMERA ===
camera = cv2.VideoCapture(0)
if not camera.isOpened():
    print("[ERRO] Câmera não encontrada!")
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

# === ESTADOS ===
estado = "START"
mostrar_camera = False
ultima_pergunta = None  # para saber de qual resposta veio CORRETO/INCORRETO
tempo_inicio_correto = None
tempo_inicio_incorreto = None

def mudar_estado(novo):
    global estado, mostrar_camera, tempo_inicio_correto, tempo_inicio_incorreto, ultima_pergunta
    print(f"[DEBUG] Mudando estado: {estado} -> {novo}")
    if "RESPOSTA" in novo:
        ultima_pergunta = novo
    estado = novo
    mostrar_camera = "RESPOSTA" in novo
    tempo_inicio_correto = None
    tempo_inicio_incorreto = None

# === LOOP PRINCIPAL ===
rodando = True
while rodando:
    # Eventos Pygame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            print(f"[DEBUG] Clique detectado no estado: {estado}")
            if estado == "START":
                mudar_estado("PERGUNTA1")
            elif estado.startswith("PERGUNTA"):
                mudar_estado(estado.replace("PERGUNTA", "RESPOSTA"))
            elif estado in ["CORRETO", "INCORRETO"]:
                # Avança conforme a última resposta
                if ultima_pergunta:
                    prox_num = int(ultima_pergunta[-1]) + 1
                    if prox_num <= 6:
                        mudar_estado(f"PERGUNTA{prox_num}")
                    else:
                        mudar_estado("START")

    # Captura da câmera
    ret, frame = camera.read()
    if not ret:
        print("[DEBUG] Falha na captura da câmera!")
        continue
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    # Detecção de dedos
    if mostrar_camera and results.multi_hand_landmarks:
        for hand_landmarks, hand_handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            hand_label = hand_handedness.classification[0].label
            dedos = contar_dedos(hand_landmarks, hand_label)
            print(f"[DEBUG] Mão detectada ({hand_label}) - Dedos: {dedos}")

            # Dedos corretos por resposta
            if estado == "RESPOSTA1":
                certos = {2}
            elif estado == "RESPOSTA2":
                certos = {4}
            elif estado == "RESPOSTA3":
                certos = {3}
            elif estado == "RESPOSTA4":
                certos = {1}
            elif estado == "RESPOSTA5":
                certos = {3}
            elif estado == "RESPOSTA6":
                certos = {2}
            else:
                certos = set()

            # Lógica de tempos separados
            if dedos in certos:
                tempo_inicio_correto = tempo_inicio_correto or time.time()
                tempo_inicio_incorreto = None
                if time.time() - tempo_inicio_correto >= TEMPO_CORRETO:
                    print("[DEBUG] Gesto correto reconhecido")
                    mudar_estado("CORRETO")
            elif dedos not in certos and dedos > 0:
                tempo_inicio_incorreto = tempo_inicio_incorreto or time.time()
                tempo_inicio_correto = None
                if time.time() - tempo_inicio_incorreto >= TEMPO_INCORRETO:
                    print("[DEBUG] Gesto incorreto reconhecido")
                    mudar_estado("INCORRETO")
            else:
                tempo_inicio_correto = None
                tempo_inicio_incorreto = None

    # Desenhar na tela
    tela = carregar_imagem(layers[estado])
    screen.blit(tela, (0, 0))

    if mostrar_camera and estado.startswith("RESPOSTA"):
        cam_surf = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
        cam_surf = pygame.transform.scale(cam_surf, (400, 300))
        screen.blit(cam_surf, (440, 200))

    pygame.display.flip()

camera.release()
pygame.quit()
