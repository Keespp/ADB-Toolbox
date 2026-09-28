import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import test_dispositivo
import test_interfaz
import test_registros
import test_tvbox

MODULOS = [test_dispositivo, test_tvbox, test_registros, test_interfaz]

def main():
    fallos = []
    for modulo in MODULOS:
        try:
            fallos += [(modulo.__name__, f) for f in modulo.correr()]
        except Exception as e:
            import traceback
            traceback.print_exc()
            fallos.append((modulo.__name__, "reventó: %s" % e))

    print("\n" + "=" * 62)
    if fallos:
        print("FALLOS: %d" % len(fallos))
        for modulo, mensaje in fallos:
            print("  · [%s] %s" % (modulo, mensaje))
    else:
        print("Todo en orden.")
    return 1 if fallos else 0

if __name__ == "__main__":
    sys.exit(main())
