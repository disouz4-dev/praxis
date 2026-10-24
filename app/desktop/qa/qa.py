#!/usr/bin/env python3
"""Cliente do modo de verificação do Praxis (PRAXIS_QA_PORTA): executa JavaScript na janela real.
Uso: qa.py <porta> 'código JS' ['código JS' ...]   (cada um vira uma linha; imprime o resultado)
     qa.py <porta> -f roteiro.js                    (uma instrução por linha; # comenta)
     qa.py <porta> -s roteiro.js                    (o arquivo inteiro como um trecho só)"""
import json, socket, sys

def main():
    porta = int(sys.argv[1]); args = sys.argv[2:]
    if args[:1] == ["-s"]:   # o arquivo inteiro é um trecho só (comentários só /* */)
        args = [open(args[1], encoding="utf-8").read()]
    elif args[:1] == ["-f"]:
        args = [l for l in open(args[1], encoding="utf-8").read().splitlines() if l.strip() and not l.lstrip().startswith("#")]
    s = socket.create_connection(("127.0.0.1", porta), timeout=130)
    f = s.makefile("rw", encoding="utf-8")
    for js in args:
        f.write(js.replace("\n", " ") + "\n"); f.flush()
        r = f.readline().strip()
        try: r = json.dumps(json.loads(json.loads(r)) if r.startswith('"') else json.loads(r), ensure_ascii=False)
        except Exception: pass
        print(r, flush=True)

if __name__ == "__main__":
    main()
