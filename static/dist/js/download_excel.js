
function preview_excel(excel_href, name_table, name_file) {
    // Используем атрибут externalHTML, чтобы получить HTML-код всего элемента таблицы (включая тег <table>), а затем упаковать его в полный HTML-документ, установить charset на urf-8, чтобы китайский не искажался
    var html = "<html><head><meta charset='utf-8' /></head><body>" + document.getElementById(name_table).outerHTML + "</body></html>";
    // Создание экземпляра объекта Blob, первым параметром его конструктора является массив, содержащий содержимое файла, а вторым параметром является объект, содержащий атрибуты типа файла
    var blob = new Blob([html], {type: "application/vnd.ms-excel"});
    var a = document.getElementById(excel_href);
    // Используйте метод URL.createObjectURL () для создания URL-адреса BLOB-объекта для элемента a
    a.href = URL.createObjectURL(blob);
    // Установить имя файла
    a.download = "" + name_file + ".xls";
};