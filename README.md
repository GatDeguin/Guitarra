# ÉBANO — V4 · Cuerdas físicas

Instrumento de guitarra pentatónica menor, pensado para el iPhone horizontal. Una posición completa por pantalla y seis cuerdas continuas hasta la pastilla derecha. El diapasón conserva la separación de los trastes en temperamento igual y la escala geométrica uniforme. El instrumento tiene 12 tonalidades × 5 posiciones y arranca en Am, posición I (5–8).

## Ejecutar

- Web: abrir `index.html` en un navegador compatible con Web Audio y Pointer Events; si iOS no ejecuta HTML local, servir la carpeta desde un servidor estático. En Safari, usar la pantalla horizontal. No hay bibliotecas, fuentes, imágenes o muestras de audio externas.
- Apoyar el teléfono, sostener las notas con la izquierda y atacar las cuerdas en la pastilla derecha. El indicador AMP permite activar o silenciar el audio. El potenciómetro VOL regula el volumen; EXP habilita articulaciones; FIJO habilita el modo de una mano/mouse; TAPA abre los ajustes. Las incrustaciones indican las notas válidas. Las cuerdas sin digitación permanecen silenciadas.
- Slide: después de atacar, mover el dedo longitudinalmente entre las notas de la misma cuerda. La altura varía de forma continua sobre la misma voz, incluyendo alturas intermedias. Bend: mover el dedo transversalmente; hasta 200 cents, con retorno al centro. Tras llegar a una nota válida, se puede pasar de slide a bend; al regresar de un bend, se puede volver a deslizar sin levantar el dedo. Ligados: apoyar o quitar un segundo dedo en la misma cuerda (hammer-on/pull-off). Con EXP apagado, sólo se permiten las alturas de la escala.
- En computadora, FIJO permite seleccionar con un clic y pulsar con mouse o teclas 1–6 (de aguda a grave). QWERTY selecciona las notas inferiores, ASDFGH las superiores, Escape silencia y las flechas cambian de posición.

## Motor físico de cuerda V4

Se reemplaza la reproducción de buffers transpuestos de la V3 por un banco modal de estado persistente, calculado en tiempo real. Cada cuerda conserva sus componentes de desplazamiento y velocidad mientras cambia la afinación. El código DSP está delimitado en `index.html` y las pruebas extraen ese mismo núcleo, no una implementación paralela.

- Hasta 48 modos primarios dispersivos y ocho modos de segunda polarización por cuerda (336 estados modales entre seis cuerdas; el filtro anti-alias elimina modos fuera de banda).
- Longitud vibrante `ell = 0.648 * 2^(-(fret + slide/100)/12)` m. Tensión nominal por cuerda y aumento ideal `T = T0 * 2^(bend/600)` N. Rigidez `B = pi² EI / (T ell²)`, con diámetros de núcleo efectivos y módulo elástico del acero de 200 GPa. `f_n = n f_1 sqrt((1+B n²)/(1+B))` conserva la fundamental afinada. El estado complejo continúa girando sin reiniciarse en un bend o slide.
- Pérdidas dependientes de frecuencia, modo, cuerda y longitud; decaimiento en tiempo real, no escalado con la velocidad de reproducción. Aproximación adiabática al trabajo de variar la afinación: la energía normalizada de un modo varía proporcionalmente a su frecuencia antes de aplicar pérdidas. Se aproxima una frontera que cambia lentamente; no resuelve la PDE completa de contacto cuerda-traste.
- Excitación triangular en el punto físico de la púa, entre 20 y 120 mm del puente, amplitud dependiente del gesto y amortiguación de la vibración previa por el contacto. Ligados aportan una excitación menor; el roce de slide y el ruido de ataque son componentes estocásticos amortiguados.
- Captación por velocidad modal, dos bobinas de posición fija (43 y 61 mm desde el puente) y apertura espacial efectiva de 9 mm; se actualiza al cambiar la longitud. La segunda polarización produce batimientos y decaimiento diferente. No se afirma replicar una pastilla comercial medida.
- Acoplamiento disipativo pasivo aproximado: `v <- v - alpha*w*(wᵀv)/||w||²`. Para `0 <= alpha <= 1`, la norma al cuadrado no aumenta, y puede haber transferencia de energía a otras cuerdas preparadas. Las cuerdas sin digitación no se excitan. No es una simulación calibrada de la impedancia compleja del puente real.
- Fricción y liberación del dedo aumentan las pérdidas; protección anti-alias modal, margen fijo de mezcla y limitador estéreo enlazado de seguridad con rodilla suave por encima de 0.84. No se normaliza cada nota. El amplificador/ambiente y controles existentes permanecen.

Los parámetros de materiales, pérdidas, tensión y contacto son hipótesis razonables de ingeniería: faltan mediciones de una guitarra física para identificarlos. El audio sigue siendo síntesis; no contiene muestras de un instrumento real.

### Rutas de ejecución

`AudioWorklet` es la vía primaria en un origen seguro compatible; el módulo se construye localmente desde el código DSP incluido en el HTML. Si no se puede cargar (por ejemplo, origen no seguro), se usa el mismo motor por `ScriptProcessorNode`, API de compatibilidad obsoleta con mayor riesgo de latencia y bloqueos del hilo principal. En último caso se mantiene la reproducción de buffers calculados por el núcleo nuevo; esta ruta extrema no ofrece toda la física dinámica. El diagnóstico `window.__guitar.snapshot()` distingue `modal-realtime`, `modal-compat` y `buffer-fallback`. No hay peticiones a recursos remotos.

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
node tests/physics.mjs
python -m pip install playwright
python -m playwright install chromium
python tests/tests.py
```

También se puede indicar `CHROMIUM_PATH` para un binario local. Resultado: 169/169 comprobaciones (119 en Chromium + 50 DSP). Se conserva `tests/resultados-pruebas.json` y `tests/resultados-fisica.json` con mediciones y entorno reproducibles.

En las 36 pruebas de afinación (6 cuerdas × 3 trastes × 2 frecuencias de muestreo), el máximo error estimado fue 0,5 cents según el estimador de búsqueda local de frecuencia. El bend de 200 cents en La2 llegó a 123,4708 Hz, y el slide de La2 a Do3 quedó a -1 cent del objetivo estimado. La diferencia RMS entre las velocidades de prueba 0,2 y 0,9 fue 13,61 dB; cambiar el punto de púa modificó la relación de energía de parciales agudos a graves en 8,89 dB. El acoplamiento transfirió energía a una cuerda preparada sin aumentar la suma de energía modal en el ensayo de tono común. En 4 segundos de estrés polifónico, el pico PCM protegido fue 0,961, y el limitador actuó en 57 de 192.000 muestras temporales estéreo. El pico previo a la protección fue 1,022; no se oculta la actuación del limitador.

El ensayo de rendimiento con Node/V8 midió una mediana de aproximadamente 0,11 ms para bloques de 128 muestras a 48 kHz (presupuesto 2,67 ms), con picos mayores en el escenario extremo. No es una medición de latencia ni rendimiento en iPhone. La prueba del navegador ejecutó Web Audio en Chromium, con el núcleo DSP real por `ScriptProcessorNode`: no se pudo abrir un origen seguro por restricciones del entorno. Se verificó el registro y proceso del módulo AudioWorklet en un host simulado, no en el hilo de audio real. Sigue pendiente comprobar AudioWorklet en un origen seguro, Safari e iPhone físico, compilar el contenedor Xcode, medir latencia y evaluar el timbre contra grabaciones controladas de guitarra.
