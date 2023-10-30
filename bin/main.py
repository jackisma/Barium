import os
import cv2
import mediapipe as mp
import math
import numpy as np
from PIL import Image, ImageDraw
import time
import datetime
import pytz
from keras.models import load_model

model = load_model("model.keras")

salvar_videos = False

fusoHorario = pytz.timezone('America/Sao_Paulo')
dia_atual = (datetime.datetime.now(fusoHorario)).strftime('%Y-%m-%d %H-%M-%S')

if salvar_videos:
    diretorio = f"../video/video_{dia_atual}"
    os.makedirs(diretorio)

intervalo = 100
quantidade_de_frames = 20

exibir_conexoes = True
mostrar_numeros = True
dataset = "../../data/test.csv"

def aumentar_contraste(frame):

    alpha = 2
    beta = 0

    imagem = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    return imagem

def calcular_distancia(ponto1, ponto2):
    return math.sqrt(((ponto2[0] - ponto1[0]) ** 2) + ((ponto2[1] - ponto1[1]) ** 2))

modo_mouse = False

cap = cv2.VideoCapture(0)
mp_maos = mp.solutions.hands
maos = mp_maos.Hands(max_num_hands=1)

while True:

    ponto_anterior = None
    matriz = None

    dados = []
    numero = -1
    iteracao = 0

    matrizes = []

    z = 0

    while True:
        coordenadas = []
        for a in range(21):
            coordenadas.append([0, 0])

        sucesso, frame = cap.read()
        if not sucesso:
            continue

        frame = cv2.flip(frame, 1)
        

        resultados = maos.process(cv2.cvtColor(aumentar_contraste(frame), cv2.COLOR_BGR2RGB))

        lista_pontos = []

        if resultados.multi_hand_landmarks:
            for pontos_mao in resultados.multi_hand_landmarks:
                for idx, ponto in enumerate(pontos_mao.landmark):
                    altura, largura, _ = frame.shape
                    cx, cy = int(ponto.x * largura), int(ponto.y * altura)
                    if mostrar_numeros:
                        cv2.putText(frame, str(idx), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    lista_pontos.append((cx, cy))

                if lista_pontos:
                    x, y, w, h = cv2.boundingRect(np.array(lista_pontos))
                    tamanho_max = max(w, h)

                    centro_x = x + w // 2
                    centro_y = y + h // 2

                    x = centro_x - tamanho_max // 2
                    y = centro_y - tamanho_max // 2

                    x, y, w, h = x - 10, y - 10, tamanho_max + 20, tamanho_max + 20

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                if exibir_conexoes:
                    mp.solutions.drawing_utils.draw_landmarks(frame, pontos_mao, mp_maos.HAND_CONNECTIONS)


        if not numero == -1 and iteracao < 20:
            tempo_atual = time.time() * 1000

            if tempo_atual - tempo_anterior >= intervalo or iteracao == 0:            
                tempo_anterior = tempo_atual

                matriz = np.full((100, 100), -1, dtype=int)
                if lista_pontos:
                    for idx, ponto in enumerate(lista_pontos):
                        x_rel = (ponto[0] - x) * 100 // w
                        y_rel = (ponto[1] - y) * 100 // h
                        valor = idx
                        matriz[y_rel][x_rel] = valor    

                iteracao += 1

        else:
            if iteracao == 20:

                dados.append(matrizes)
                iteracao = -1
                numero = -1
                matrizes = []

                valor_video = " "

                if salvar_videos:
                    video.release()
                    valor_video += "e vídeo "
                
                print(f"Dados{valor_video}registrados!")

            key = cv2.waitKey(1) & 0xFF


            if key in range(ord('0'), ord('9') + 1) and lista_pontos:
                numero = chr(key)

                tempo_anterior = time.time() * 1000 

                if salvar_videos:
                    m_video = f'{diretorio}/video_{z}.mp4'
                    duracao_frame = 10

                    pre = cv2.VideoWriter_fourcc(*'mp4v')
                    video = cv2.VideoWriter(m_video, pre, duracao_frame, (100, 100))


                z += 1
                print(z)

        if matriz is not None:
            for linha in range(matriz.shape[0]):
                for coluna in range(matriz.shape[1]):
                    elemento = matriz[coluna, linha]
                    if elemento != -1:
                        coordenadas[elemento] = [linha, coluna]

            foto = Image.new("RGB", (100, 100), "black")

            draw = ImageDraw.Draw(foto)

            for indice, (x,y) in enumerate(coordenadas):
                draw.text((x,y), str("."), fill="white")

            foto = np.array(foto)
            foto = cv2.resize(foto, (100, 100))
            
            if salvar_videos:
                video.write(foto)

            matriz = None
            diagonal = calcular_distancia((x, y), (x + w, y + h))
            referencial = ((x + w, y + h))

            linha = []

            for [x, y] in coordenadas:
                linha.append([x, y])

            matrizes.append(linha)

        cv2.imshow("Câmera", aumentar_contraste(frame))

        if iteracao == -1:
            iteracao = 0
            break

    dados = np.array(dados)

    video = (dados).reshape((1, 840))

    previsoes = model.predict(video)

    movimentos = ['Fechar Telas', 'Print screen', 'Ativar modo mouse virtual', 'Aumentar o volume', 'Salvar', 'Abrir o explorador de arquivos', 'Diminuir o volume', 'Aumentar o brilho', 'Diminuir o brilho', 'Control + Z', 'Control + Y', 'Confirmar']

    max_move = max(len(x) for x in movimentos)

    previsoes_tratadas = []

    maior = 0

    for i, previsao in enumerate(previsoes[0]):
        if previsao > previsoes[0][maior]:
            maior = i

        previsoes_tratadas.append(f"{previsao * 100:.2f}%")

    
    max_pred = max(len(x) for x in previsoes_tratadas)

    print( "┌" + "─" * (max_move + 2) + "┬" + "─" * (max_pred + 2) + "┐")
    
    for i, previsao in enumerate(previsoes_tratadas):
        if i != maior:
            if (previsoes[0][i] * 100) > 10:
                print(f"│ {movimentos[i]}" + " " * (max_move - len(movimentos[i]) + 1) + "│" + f" \033[34m{previsao}\033[0m" + " " *  (max_pred - len(previsao) + 1) + "│")
            else:
                print(f"│ {movimentos[i]}" + " " * (max_move - len(movimentos[i]) + 1) + "│" + f" {previsao}" + " " *  (max_pred - len(previsao) + 1) + "│")
        else:
            print(f"│ \033[32m{movimentos[i]}\033[0m" + " " * (max_move - len(movimentos[i]) + 1) + "│" + f" \033[32m{previsao}\033[0m" + " " *  (max_pred - len(previsao) + 1) + "│")

        if i < (len(previsoes_tratadas) - 1):
            print( "├" + "─" * (max_move + 2) + "┼" + "─" * (max_pred + 2) + "┤")

    
    print( "└" + "─" * (max_move + 2) + "┴" + "─" * (max_pred + 2) + "┘")

    previsao = np.argmax(previsoes)
    print("\nMovimento previsto com maior certeza: ", movimentos[previsao])

    input_v = 1

    if input_v == '0':
        exit

        cap.release()
        cv2.destroyAllWindows()