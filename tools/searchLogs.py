#!/usr/bin/env python3
"""
Script equivalente a: grep -C <n> "<patron>" <fichero>
Uso: python searchLogs.py  <fichero> <patron> [--context N]
     searchLogs.py  <fichero> <patron> [--context N] [--ignore-case]
"""

import argparse
import sys


def grep_with_context(filepath: str, pattern: str, context: int) -> None:
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: No se encontró el fichero '{filepath}'", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error al leer el fichero: {e}", file=sys.stderr)
        sys.exit(1)

    # Índices de líneas que contienen el patrón
    matches = [i for i, line in enumerate(lines) if pattern in line]

    if not matches:
        print(f"No se encontraron coincidencias para '{pattern}' en '{filepath}'")
        sys.exit(1)

    # Calcular rangos a imprimir (fusionando rangos solapados)
    ranges = []
    for idx in matches:
        start = max(0, idx - context)
        end = min(len(lines) - 1, idx + context)
        if ranges and start <= ranges[-1][1] + 1:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
        else:
            ranges.append((start, end))

    # Imprimir resultados
    total_matches = len(matches)
    print(f"Fichero : {filepath}")
    print(f"Patrón  : {pattern}")
    print(f"Contexto: {context} línea(s) | Coincidencias: {total_matches}\n")
    print("=" * 70)

    prev_end = -1
    for start, end in ranges:
        if prev_end != -1:
            print("--")  # separador entre bloques (igual que grep)
        for i in range(start, end + 1):
            line_num = i + 1
            marker = ">>>" if pattern in lines[i] else "   "
            print(f"{marker} {line_num:>6}: {lines[i]}", end="")
        prev_end = end

    print("\n" + "=" * 70)
    print(f"Total de coincidencias: {total_matches}")


def main():
    parser = argparse.ArgumentParser(
        description="Busca un patrón en un fichero de log mostrando líneas de contexto (equivalente a grep -C).",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Ejemplo:\n  searchLogs.py MUSOLSONG_2026-02-24_11-44-19.log CRITICAL --context 2"
    )
    parser.add_argument("fichero", help="Ruta al fichero de log")
    parser.add_argument("patron", help="Patrón de búsqueda (sensible a mayúsculas)")
    parser.add_argument(
        "-C", "--context",
        type=int,
        default=1,
        metavar="N",
        help="Número de líneas de contexto antes y después de cada coincidencia (default: 1)"
    )
    parser.add_argument(
        "-i", "--ignore-case",
        action="store_true",
        help="Búsqueda sin distinción de mayúsculas/minúsculas"
    )

    args = parser.parse_args()

    if args.context < 0:
        print("Error: el número de líneas de contexto debe ser >= 0", file=sys.stderr)
        sys.exit(1)

    patron = args.patron
    if args.ignore_case:
        # Normalizar para búsqueda case-insensitive
        try:
            with open(args.fichero, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: No se encontró el fichero '{args.fichero}'", file=sys.stderr)
            sys.exit(1)

        patron_lower = patron.lower()
        matches = [i for i, line in enumerate(lines) if patron_lower in line.lower()]

        if not matches:
            print(f"No se encontraron coincidencias para '{patron}' en '{args.fichero}'")
            sys.exit(1)

        context = args.context
        ranges = []
        for idx in matches:
            start = max(0, idx - context)
            end = min(len(lines) - 1, idx + context)
            if ranges and start <= ranges[-1][1] + 1:
                ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
            else:
                ranges.append((start, end))

        print(f"Fichero : {args.fichero}")
        print(f"Patrón  : {patron} (sin distinción may/min)")
        print(f"Contexto: {context} línea(s) | Coincidencias: {len(matches)}\n")
        print("=" * 70)

        prev_end = -1
        for start, end in ranges:
            if prev_end != -1:
                print("--")
            for i in range(start, end + 1):
                marker = ">>>" if patron_lower in lines[i].lower() else "   "
                print(f"{marker} {i+1:>6}: {lines[i]}", end="")
            prev_end = end

        print("\n" + "=" * 70)
        print(f"Total de coincidencias: {len(matches)}")
    else:
        grep_with_context(args.fichero, patron, args.context)


if __name__ == "__main__":
    main()
