"""Pruebas reproducibles: Chromium con pantalla táctil emulada (CDP), HTML sin red."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json, math, time, statistics, os, shutil
BASE=Path(__file__).resolve().parent.parent
HTML=(BASE/'index.html').read_text()
CAPTURES=BASE/'capturas'; CAPTURES.mkdir(exist_ok=True)
checks=[]
def check(name,cond,detail=''):
    checks.append(dict(prueba=name,resultado='PASS' if cond else 'FAIL',detalle=str(detail)))
    print(('PASS' if cond else 'FAIL'),name,detail)
    if not cond: raise AssertionError(f'{name}: {detail}')
with sync_playwright() as w:
    executable=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or shutil.which('chromium-browser')
    browser=w.chromium.launch(**({'executable_path':executable} if executable else {}),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':852,'height':393},device_scale_factor=1,has_touch=True,is_mobile=True)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    requests=[];page.on('request',lambda r:requests.append(r.url))
    page.set_content(HTML,wait_until='domcontentloaded');page.wait_for_timeout(350)
    def js(s): return page.evaluate(s)
    def snap(): return js('window.__guitar.snapshot()')
    def geom(): return js('window.__guitar.geometry()')
    def attacks(): return [e for e in snap()['events'] if e['type']=='attack']
    def last(n=1):return attacks()[-n:]
    def boxnote(s,f):return next(n for n in geom()['notes'] if n['s']==s and n['f']==f)
    def pick(s):return next(n for n in geom()['pick'] if n['s']==s)
    def absolute(p):
        r=page.locator('#play').bounding_box();return {'x':r['x']+p['x'],'y':r['y']+p['y']}
    session=page.context.new_cdp_session(page);session.send('Emulation.setTouchEmulationEnabled',{'enabled':True,'maxTouchPoints':10})
    touches={}
    def send(event):
        session.send('Input.dispatchTouchEvent',{'type':event,'touchPoints':[{'id':k,'x':p['x'],'y':p['y'],'radiusX':5,'radiusY':5,'force':.6} for k,p in touches.items()]});page.wait_for_timeout(24)
    def touch(i,p):touches[i]=absolute(p);send('touchStart')
    def move(i,p):touches[i]=absolute(p);send('touchMove')
    def end(i):
        p=touches.pop(i);session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[{'id':i,'x':p['x'],'y':p['y']}]});page.wait_for_timeout(24)
    def cancel():touches.clear();send('touchCancel')
    check('Inicio sin excepciones',not errors,errors)
    allboxes=js('window.__guitar.allBoxes()');count=0
    for r,forms in enumerate(allboxes):
        prev=0
        for f,b in enumerate(forms):
            good=(len(b['notes'])==12 and len({(n['s'],n['f']) for n in b['notes']})==12 and all((n['midi']-r)%12 in [0,3,5,7,10] for n in b['notes']) and all(len(a)==2 for a in b['frets']) and 1<=b['lo']<=b['hi']<=24 and b['lo']>prev)
            check(f'Mapa tonalidad {r} posición {f+1}',good,f"T{b['lo']}–{b['hi']}")
            prev=b['lo'];count+=1
    check('60 configuraciones musicales, 720 notas',count==60)
    expected=[[5,8],[5,8],[5,7],[5,7],[5,7],[5,8]]
    check('Am posición I exacta',snap()['box']['frets']==expected)
    check('Am I contiene tres tónicas',sum(n['root'] for n in snap()['box']['notes'])==3)
    g=geom();gaps=[b-a for a,b in zip(g['frets'],g['frets'][1:])]
    check('Geometría: progresión 2^(-1/12)',all(abs(gaps[i+1]/gaps[i]-2**(-1/12))<1e-10 for i in range(len(gaps)-1)))
    check('Geometría: misma escala longitudinal y transversal',abs(g['width1']/g['scale']-(43+15*(648*(1-2**(-8/12)))/(648*(1-2**(-24/12)))))<1e-9)
    check('No recursos remotos',not [r for r in requests if r.startswith(('http:','https:'))],requests[:3])
    page.get_by_role('button',name='Activar sonido').click();page.wait_for_timeout(1600)
    check('AudioContext real activado',snap()['audio']=='running')
    check('12 buffers de notas precargados',snap()['cache']>=12,snap()['cache'])
    # real multi-touch input, not synthetic PointerEvent dispatch
    before=len(attacks());touch(10,boxnote(5,5))
    check('Mano izquierda prepara La2 sin atacar',snap()['current'][5]==5 and len(attacks())==before,snap()['current'])
    touch(20,pick(5));page.wait_for_timeout(100)
    check('Dos manos: púa ataca La2',len(attacks())==before+1 and last()[0]['midi']==45,last())
    level=js('window.__guitar.signal()');check('Señal de audio real en el grafo Web Audio',level is not None and level>.001,level)
    page.screenshot(path=str(CAPTURES/'guitarra-v3-activa.png'))
    end(20);check('Soltar púa conserva nota pisada',snap()['current'][5]==5 and snap()['voices'][5] is not None)
    end(10);check('Soltar mano izquierda libera voz',all(v is None for v in snap()['voices']) and all(v is None for v in snap()['current']))
    # Invalid fret 6, choose same y as its string (midpoint interpolation).
    g=geom();bad={'x':(g['frets'][1]+g['frets'][2])/2,'y':boxnote(3,5)['y']};before=len(attacks());touch(1,bad);touch(2,pick(3));check('Traste 6 silencioso',len(attacks())==before and snap()['current'][3] is None);cancel()
    # All strings prepared, sweep in a single jump, verify crossing order.
    for s in range(6):touch(100+s,boxnote(s,5))
    check('Seis contactos simultáneos conservan seis notas',snap()['current']==[5]*6,snap()['current'])
    before=len(attacks());touch(200,pick(0));move(200,pick(5));page.wait_for_timeout(50)
    seq=attacks()[before:];check('Barrido rápido descendente procesa seis cuerdas en orden',[e['s'] for e in seq]==list(range(6)),[e['s'] for e in seq])
    before=len(attacks());move(200,pick(0));page.wait_for_timeout(35)
    seq=attacks()[before:];check('Barrido inverso sin repetir cuerda inicial',[e['s'] for e in seq]==[4,3,2,1,0],[e['s'] for e in seq])
    before=len(attacks());p0=pick(0);p1=pick(1);j={'x':p0['x'],'y':p0['y']+.55*(p1['y']-p0['y'])};move(200,j);move(200,p0);check('Histéresis evita ataques por temblor',len(attacks())==before)
    cancel();check('TouchCancel limpia todas las cuerdas',all(v is None for v in snap()['voices']) and all(v is None for v in snap()['current']) and not snap()['pointers'])
    # Legato and bend
    touch(1,boxnote(5,5));touch(2,pick(5));end(2);touch(3,boxnote(5,8));check('Hammer-on con segunda digitación',last()[0]['kind']=='hammer' and last()[0]['f']==8,last())
    end(3);check('Pull-off retorna al dedo inferior',last()[0]['kind']=='pull' and last()[0]['f']==5,last())
    p=boxnote(5,5);move(1,{'x':p['x'],'y':p['y']-22});b=snap()['bends'][5];check('Bend cambia afinación de voz en tiempo real',b>50 and abs(snap()['voices'][5]['bend']-b)<.01,b)
    move(1,p);check('Bend vuelve a afinación original',snap()['bends'][5]<1)
    cancel()
    # Slide and compound gestures: same sounding string and serial, no new attack.
    p0=boxnote(5,5);p1=boxnote(5,8);touch(1,p0);touch(2,pick(5));end(2);n0=len(attacks());v0=snap()['voices'][5]['serial']
    mid={'x':p0['x']+(p1['x']-p0['x'])*.47,'y':p0['y']+(p1['y']-p0['y'])*.47};move(1,mid);sv=snap()
    check('Slide intermedio conserva una sola voz y altura continua',sv['voices'][5]['serial']==v0 and len(attacks())==n0 and 75<sv['voices'][5]['pitchCents']<225,sv['voices'][5])
    move(1,p1);sv=snap();check('Slide llega a Do3 sin reataque',sv['current'][5]==8 and abs(sv['voices'][5]['pitchCents']-300)<5 and sv['voices'][5]['serial']==v0 and len(attacks())==n0,sv['voices'][5])
    move(1,{'x':p1['x'],'y':p1['y']-24});sv=snap();check('Slide seguido de bend sin levantar dedo ni reataque',sv['bends'][5]>60 and sv['voices'][5]['pitchCents']>360 and sv['voices'][5]['serial']==v0 and len(attacks())==n0,sv['voices'][5])
    move(1,p1);sv=snap();check('Release de bend conserva altura del destino del slide',sv['bends'][5]<1 and abs(sv['voices'][5]['pitchCents']-300)<5,sv['voices'][5])
    move(1,p0);sv=snap();check('Bend seguido de slide inverso sobre la misma voz',sv['current'][5]==5 and abs(sv['voices'][5]['pitchCents'])<5 and sv['voices'][5]['serial']==v0 and len(attacks())==n0,sv['voices'][5])
    cancel();check('Slide y bend terminan sin voces retenidas',not any(snap()['voices']))
    # Real JS bridge with mock native receiver; not a physical haptic test.
    js("window.__nativeHapticsSupported=true;window.webkit={messageHandlers:{guitarHaptic:{postMessage:o=>{(window.__hapticTest||(window.__hapticTest=[])).push(o)}}}}")
    touch(1,p0);touch(2,pick(5));end(2);move(1,p1);move(1,{'x':p1['x'],'y':p1['y']-26});cancel()
    he=js('window.__hapticTest||[]');check('Puente nativo emite ataques y articulaciones',{'fret','pick','slide','bend'}<=set(e['kind'] for e in he),he)
    check('Parámetros hápticos finitos y acotados',all(.05<=e['intensity']<=1 and .05<=e['sharpness']<=1 for e in he))
    js('window.__nativeHapticsSupported=false;delete window.webkit');check('Sin capacidad nativa no se declara Core Haptics',snap()['haptics']['mode']!='Core Haptics')
    page.locator('#express').click()
    # Keyboard and mouse/one-handed mode
    page.locator('#hold').click();p=absolute(boxnote(0,5));page.mouse.click(p['x'],p['y']);check('Modo Fijar mantiene nota tras levantar mouse',snap()['current'][0]==5)
    before=len(attacks());page.keyboard.press('1');page.wait_for_timeout(25);check('Teclado 1 ataca primera cuerda fijada',len(attacks())==before+1 and last()[0]['s']==0)
    page.keyboard.press('a');check('Teclado A elige segundo traste de la primera cuerda',snap()['current'][0]==8)
    page.keyboard.press('Escape');check('Escape limpia todas las notas',all(v is None for v in snap()['current']))
    page.locator('#hold').click()
    # Settings and position switching
    page.get_by_role('button',name='Ajustes de instrumento').click();page.get_by_role('button',name='Ambient',exact=True).click();page.get_by_role('button',name='Intervalos',exact=True).click();page.get_by_role('button',name='Grave arriba').click();page.locator('#pickWidth').fill('18');page.get_by_role('button',name='Cerrar ajustes').click()
    cfg=snap()['config'];check('Controles de timbre, guía, orientación y ancho',cfg['preset']=='ambient' and cfg['guide']=='intervals' and cfg['orientation']=='real' and cfg['pickWidth']==18,cfg)
    g=geom();check('Orientación grave arriba invierte dibujo y púa',pick(5)['y']<pick(0)['y'])
    page.get_by_role('button',name='Posición 3',exact=True).click();check('Posición III conserva cinco espacios',snap()['box']['lo']==9 and snap()['box']['hi']==13 and len(geom()['frets'])==6)
    page.locator('#key').select_option('0');check('Cambio de tonalidad a Do menor',snap()['box']['root']==0 and snap()['box']['lo']==12)
    page.get_by_role('button',name='Posición 4',exact=True).click();check('Posición IV de Do menor continúa ascendente',snap()['box']['lo']==15)
    page.get_by_role('button',name='Ajustes de instrumento').click();page.locator('#octave').check();check('Opción de octava baja mantiene clases de altura',snap()['box']['lo']==3 and all((n['midi']-0)%12 in [0,3,5,7,10] for n in snap()['box']['notes']))
    page.locator('#octave').uncheck();page.get_by_role('button',name='Clean',exact=True).click();page.get_by_role('button',name='Notas',exact=True).click();page.get_by_role('button',name='Aguda arriba').click();page.locator('#pickWidth').fill('14');page.get_by_role('button',name='Cerrar ajustes').click();page.locator('#key').select_option('9');page.get_by_role('button',name='Posición 1',exact=True).click()
    # Demo and cancellation
    before=len(attacks());page.get_by_role('button',name='Demostrar escala').click();page.wait_for_timeout(420);check('Demostración inicia en nota grave',len(attacks())>before and attacks()[before]['midi']==45)
    page.get_by_role('button',name='Detener demostración').click();before=len(attacks());page.wait_for_timeout(420);check('Demo se cancela sin ataques tardíos',len(attacks())==before and not snap()['demoRunning'])
    # Sample validation in actual JS engine; autocorrelation for A2.
    audio_test=js('''()=>{let a=window.__guitar.synth(5,45,44100);let finite=a.every(Number.isFinite);let peak=0;for(let v of a)peak=Math.max(peak,Math.abs(v));let rms=(i,n)=>Math.sqrt(a.slice(i,i+n).reduce((s,v)=>s+v*v,0)/n);let best={lag:0,c:-1e10};for(let lag=390;lag<=412;lag++){let x=0,y=0,z=0;for(let i=9000;i<12000;i++){x+=a[i]*a[i+lag];y+=a[i]*a[i];z+=a[i+lag]*a[i+lag]}let c=x/Math.sqrt(y*z);if(c>best.c)best={lag,c}}return {finite,peak,early:rms(3000,8000),late:rms(a.length-12000,8000),freq:44100/best.lag,corr:best.c}}''')
    check('Síntesis con amplitud acotada y datos finitos',audio_test['finite'] and .1<audio_test['peak']<1,audio_test)
    check('Frecuencia sintetizada de La2 cerca de 110 Hz',abs(audio_test['freq']-110)<1,audio_test['freq'])
    check('Decaimiento físico de amplitud',audio_test['late']<audio_test['early']*.4,(audio_test['early'],audio_test['late']))
    sizes=[(667,375),(736,414),(780,360),(844,390),(852,393),(932,430),(1024,768),(1180,820)]
    for ww,hh in sizes:
        page.set_viewport_size({'width':ww,'height':hh});page.wait_for_timeout(80);g=geom()
        safe=all(g['x0']<=n['x']<=g['x1'] and 0<n['y']<g['H'] for n in g['notes']) and 0<=g['x0']<g['x1']<g['px']<g['x2']<=g['W'] and g['scale']>0
        overflow=js('document.documentElement.scrollWidth>innerWidth || document.documentElement.scrollHeight>innerHeight')
        check(f'Encuadre horizontal {ww}×{hh}',safe and not overflow,f"escala {g['scale']:.3f}; ancho púa {g['pWidth'] if 'pWidth' in g else g['x2']-g['px']:.1f}")
        if ww==667:page.screenshot(path=str(CAPTURES/'guitarra-v3-se.png'))
    page.set_viewport_size({'width':852,'height':393});page.wait_for_timeout(350);page.screenshot(path=str(CAPTURES/'guitarra-v3-preview.png'))
    page.set_viewport_size({'width':393,'height':852});page.wait_for_timeout(150);check('Pantalla vertical pide rotar',page.locator('#rotate').is_visible())
    check('Sin excepciones durante las pruebas',not errors,errors)
    check('Sin recursos HTTP externos durante pruebas',not [r for r in requests if r.startswith(('http:','https:'))])
    browser.close()
report={'entorno':'Chromium headless con Playwright + CDP; touch emulado; HTML cargado como contenido (sin navegación file://).','total':len(checks),'aprobadas':sum(x['resultado']=='PASS' for x in checks),'pruebas':checks,'limitaciones':['No iPhone físico','No latencia dedo-altavoz medida','No escucha subjetiva del timbre','No Safari físico ni WebKit disponible en esta ejecución']}
(BASE/'tests'/'resultados-pruebas.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)); print('TOTAL',report['total'])
