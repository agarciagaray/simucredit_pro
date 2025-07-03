# SimuCredit Pro

SimuCredit Pro es una aplicación web desarrollada en Django para la simulación de créditos, gestión de perfiles de crédito y administración de usuarios. Permite a los usuarios simular préstamos, ver detalles de amortización y a los administradores configurar perfiles y gestionar usuarios de manera sencilla y segura.

## Características principales
- Simulación de créditos con cálculo de amortización y desglose de cargos.
- Gestión de perfiles de crédito (CRUD) solo para administradores.
- Gestión de usuarios (CRUD) y asignación de roles (usuario o administrador).
- Interfaz moderna y responsiva.
- Exportación de reportes en Excel y PDF.
- Autenticación y control de acceso por roles.

## Estructura del proyecto
```
simucredit_project/
├── manage.py
├── settings.py
├── urls.py
├── requirements.txt
├── simulator/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── ...
├── templates/
│   ├── base.html
│   ├── simulator.html
│   ├── perfiles.html
│   ├── usuarios.html
│   └── ...
├── static/
│   └── js/
│       └── main.js
└── ...
```

## Instalación y configuración
1. **Clona el repositorio y entra al directorio del proyecto:**
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd simucredit_project
   ```
2. **Crea y activa un entorno virtual:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux/Mac
   .venv\Scripts\activate    # En Windows
   ```
3. **Instala las dependencias:**
   ```bash
   python -m pip install -r requirements.txt
   ```
4. **Aplica las migraciones:**
   ```bash
   python manage.py migrate
   ```
5. **Crea un superusuario para acceder al panel de administración:**
   ```bash
   python manage.py createsuperuser
   ```
6. **Inicia el servidor de desarrollo:**
   ```bash
   python manage.py runserver
   ```
7. **Accede a la aplicación:**
   - Simulador: [http://localhost:8000/](http://localhost:8000/)
   - Admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)

## Dependencias principales
- Django >= 5.2
- pandas
- openpyxl
- weasyprint
- python-decouple

## Uso
- **Usuarios administradores** pueden gestionar perfiles de crédito y usuarios desde el menú superior.
- **Usuarios normales** solo pueden simular créditos.
- El acceso a la administración está protegido por autenticación y roles.

## Contacto y créditos
- **Autor:** Alejandro García Garay
- **Correo:** agarciagaray@pm.me

Si tienes dudas, sugerencias o encuentras algún problema, no dudes en contactarme.

---

¡Gracias por usar SimuCredit Pro!