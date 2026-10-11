/* Farbschema vor dem ersten Zeichnen setzen (kein Aufblitzen). Auto = System. */
(function () { try { var t = localStorage.getItem('cn-theme'); if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t); } catch (e) { /* Speicher gesperrt */ } })();
