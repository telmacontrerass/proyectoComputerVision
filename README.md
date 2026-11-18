# proyectoComputerVision

El proyecto implementa unos ejercicios de entrenamiento de la precisión en la conducción. Una cámara enfoca el volante y la aplicación va interpretando sus giros en tiempo real.

# Objetivo
Entrenar la precisión de giro. En cada ronda, el jugador debe girar el volante hasta superponer sus marcas con las referencias que aparecen en pantalla. La diferencia entre el ángulo solicitado y el realizado permite medir cuánto le ha faltado para alcanzar el objetivo o cuánto se ha pasado.

# Funcionamiento previsto
1. # Acceso mediante una secuencia de colores
   El jugador tiene que colocar, por turnos, una marca de cada color dentro de un recuadro y la mantiene ahí unos segundos.    Esta contraseña sirve para permitir al jugador acceder al juego y también para comprobar que la cámara distingue bien       las marcas antes de empezar.
2. # Modo entrenamiento
   La pantalla va mostrando las posiciones objetivo junto con las marcas detectadas. El sistema localiza el centro de cada     marca y estima el giro a partir de la orientación de la línea que las une. Cuando las marcas coinciden con sus objetivos    dentro del margen admitido, se completa la ronda.

3. # Modo avanzado de conducción
   Como ampliación, el giro del volante controlará un coche en un circuito virtual. Completar el recorrido sumará puntos y una colisión devolverá el coche a la salida


# PRÓXIMOS PASOS
-Validar la detección de colores y la estimación de ángulos con el volante real
-Ajustar el tiempo de la contraseña visual y el margen de acierto del entrenamiento
-Incorporar el circuito, las colisiones y la puntuación del modo avanzado
-Documentar las dependencias y el comando de ejecución una vez probados
-Añadir un vídeo de demostración con la tasa de fotogramas por segundo (FPS) visible

   
