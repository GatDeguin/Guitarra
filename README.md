# ÉBANO — V3

Instrumento de guitarra pentatónica menor, pensado para el iPhone horizontal. Una posición completa por pantalla y seis cuerdas continuas hasta la pastilla derecha. El diapasón conserva la separación de los trastes en temperamento igual y la escala geométrica uniforme. El instrumento tiene 12 tonalidades × 5 posiciones y arranca en Am, posición I (5–8).

## Ejecutar

- Web: abrir `index.html` en un navegador compatible con Web Audio y Pointer Events; si iOS no ejecuta HTML local, servir la carpeta desde un servidor estático. En Safari, usar la pantalla horizontal. No hay bibliotecas, fuentes, imágenes o muestras de audio externas.
- Apoyar el teléfono, sostener las notas con la izquierda y atacar las cuerdas en la pastilla derecha. El indicador AMP permite activar o silenciar el audio. El potenciómetro VOL regula el volumen; EXP habilita articulaciones; FIJO habilita el modo de una mano/mouse; TAPA abre los ajustes. Las incrustaciones indican las notas válidas. Las cuerdas sin digitación permanecen silenciadas.
- Slide: después de atacar, mover el dedo longitudinalmente entre las notas de la misma cuerda. La altura varía de forma continua sobre la misma voz, incluyendo alturas intermedias. Bend: mover el dedo transversalmente; hasta 200 cents, con retorno al centro. Tras llegar a una nota válida, se puede pasar de slide a bend; al regresar de un bend, se puede volver a deslizar sin levantar el dedo. Ligados: apoyar o quitar un segundo dedo en la misma cuerda (hammer-on/pull-off). Con EXP apagado, sólo se permiten las alturas de la escala.
- En computadora, FIJO permite seleccionar con un clic y pulsar con mouse o teclas 1–6 (de aguda a grave). QWERTY selecciona las notas inferiores, ASDFGH las superiores, Escape silencia y las flechas cambian de posición.

## Sonido y aspecto

Síntesis local de cuerdas eléctricas mediante hasta 36 parciales, rigidez, posición de pastilla, ataque de púa, decaimientos por cuerda, resonancia y amortiguación. El grafo Web Audio incluye timbre dependiente del gesto, saturación suave, filtros y ambiente. No son grabaciones de una guitarra real ni un modelo de amplificador calibrado contra hardware. Las muestras sintetizadas se precargan; los slides modifican la afinación de la voz activa sin reataque. Las cuerdas muestran tensión y vibración, y los controles se integran en la placa metálica del instrumento.

## Háptica nativa iOS

La versión web sólo usa la Vibration API si está disponible; no promete vibración personalizada en Safari de iPhone. El puente Swift incluido en `ios/` recibe eventos de digitación, ataque, slide, bend y ligado e invoca transitorios de Core Haptics con intensidad y nitidez variables. Es un contenedor nativo para el mismo instrumento web, no un motor de audio nativo. Detecta soporte de hardware. No reproduce resistencia física de la cuerda.

Para construir en un Mac con Xcode y XcodeGen instalados:

```sh
cd ios
xcodegen generate
open Ebano.xcodeproj
```

Configurar el equipo de firma y un identificador de bundle propio en Xcode, seleccionar un iPhone compatible y ejecutar. Si no se usa XcodeGen, crear una app SwiftUI iOS 16+, reemplazar su punto de entrada por `EbanoApp.swift`, añadir `index.html` a Copy Bundle Resources y configurar las dos orientaciones landscape del iPhone en el target. No se distribuye un IPA ni se afirma que el contenedor haya sido compilado con el SDK de iOS: en este entorno sólo se verificó la sintaxis de Swift y el contrato de mensajes del puente en navegador emulado.

## Pruebas

```sh
python -m pip install playwright
python -m playwright install chromium
python tests/tests.py
```

También se puede indicar `CHROMIUM_PATH` para un binario local. La ejecución usa Chromium headless y Chrome DevTools Protocol para multitouch emulado. Se aprobaron 119 comprobaciones de música, geometría, contactos, barridos, audio, slides, bends, articulaciones encadenadas y contrato háptico; se incluyen resultados y capturas. La señal de audio se midió dentro del grafo Web Audio, no en la salida física. Pendientes: Safari y iPhone físicos, compilación con Xcode, evaluación perceptual del timbre y háptica, y medición de latencia de contacto a sonido y vibración.
