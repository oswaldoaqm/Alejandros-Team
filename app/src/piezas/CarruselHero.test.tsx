import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CarruselHero, DESTINOS_HERO } from "./CarruselHero";

const titulo = () => screen.getByRole("heading", { level: 2 }).textContent;
const fotos = (raiz: HTMLElement) => raiz.querySelectorAll("img.carrusel-hero__fondo").length;

describe("el carrusel de la portada", () => {
  it("pasa solo cada 6,5 segundos, y se pausa al pasar el puntero o interactuar", () => {
    vi.useFakeTimers();
    const { container } = render(<CarruselHero />);
    expect(titulo()).toBe(DESTINOS_HERO[0]?.titulo);
    act(() => vi.advanceTimersByTime(6500));
    expect(titulo()).toBe(DESTINOS_HERO[1]?.titulo);

    const seccion = container.querySelector(".carrusel-hero");
    if (seccion) fireEvent.mouseEnter(seccion);
    act(() => vi.advanceTimersByTime(20000));
    expect(titulo()).toBe(DESTINOS_HERO[1]?.titulo);

    if (seccion) fireEvent.mouseLeave(seccion);
    act(() => vi.advanceTimersByTime(6500));
    expect(titulo()).toBe(DESTINOS_HERO[2]?.titulo);
  });

  it("si se pidió menos movimiento, arranca detenido y pide solo la foto que se ve", () => {
    vi.useFakeTimers();
    vi.stubGlobal("matchMedia", (consulta: string) => ({
      matches: consulta.includes("reduce"),
      media: consulta,
    }));
    const { container } = render(<CarruselHero />);
    expect(fotos(container)).toBe(1);
    act(() => vi.advanceTimersByTime(20000));
    expect(titulo()).toBe(DESTINOS_HERO[0]?.titulo);
  });

  it("mientras pasa sola pide la foto que se ve y la que sigue, no las cinco, y nombra a su autor", () => {
    const { container } = render(<CarruselHero />);
    expect(fotos(container)).toBe(2);
    const credito = screen.getByRole("link", { name: "Foto: gertrudis2010, en Wikimedia Commons" });
    expect(credito.getAttribute("href")).toBe(
      "https://commons.wikimedia.org/wiki/File:Cusco%2C_Sacsayhuam%C3%A1n_-_panoramio.jpg",
    );
    expect(screen.getByRole("link", { name: "CC BY-SA 3.0" }).getAttribute("href")).toBe(
      "https://creativecommons.org/licenses/by-sa/3.0",
    );

    fireEvent.click(screen.getByRole("button", { name: "Siguiente destino" }));
    expect(fotos(container)).toBe(3);
    expect(screen.getByRole("link", { name: "Foto: Uwebart, en Wikimedia Commons" })).toBeTruthy();
  });

  it("su botón abre el viaje a la zona de la diapositiva", () => {
    const elegir = vi.fn();
    render(<CarruselHero onElegirDestino={elegir} />);
    fireEvent.click(screen.getByRole("button", { name: "Explorar Cusco" }));
    expect(elegir).toHaveBeenCalledWith(36);
  });
});
