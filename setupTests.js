
// setupTests.js
import '@testing-library/jest-dom'; // Importa métodos de aserción personalizados de Jest para interactuar con el DOM

// Define una función global gettext para internacionalización, si es necesaria
global.gettext = (text) => text;
