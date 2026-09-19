
## Cómo trabajamos (Oscar y Helbert)

Dos personas cambian este proyecto, cada una con su propio Claude, y las dos suben directo a la rama principal. Para no pisarse:

1. **Al abrir la sesión ya se trajo lo último de GitHub** (lo hace solo `.claude/settings.json`). Si al empezar aparece un error de ese paso, resuélvelo antes de tocar nada.
2. **Antes de cada commit, `git pull --rebase`.** Si hay conflicto, júntalo conservando el trabajo de los dos. Si no está claro cuál va, pregunta.
3. **Antes de subir, comprueba que el proyecto compila** (el `build` o `typecheck` del proyecto). Si falla, no subas.
4. **Commits pequeños y seguidos**, con un mensaje en español que diga qué cambió y por qué: el otro se entera leyendo la lista de cambios.
5. **Nunca `git push --force`** ni reescribir la historia de la rama principal.
6. **Base de datos** (migraciones, tablas, borrar datos): antes de aplicarlo, avisa al usuario para que lo coordine con el otro. Es lo único que no se deshace con un clic.
7. **Llaves y contraseñas nunca en el código**: van en las variables de Vercel.
8. **Si algo se rompe en producción**: primero volver a la versión anterior en Vercel, después arreglar con calma.
