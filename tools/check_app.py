# -*- coding: utf-8 -*-
"""
Прогоняет модули приложения в движке JS с заглушками браузера.

Проверки синтаксиса и имён ловят опечатки, но не ловят то, из-за чего
мини-апп встаёт совсем: ошибку при выполнении верхнего уровня модуля или
несостыковку экспортов. Здесь модули собираются в один скрипт в порядке
зависимостей и выполняются по-настоящему.

DOM тут игрушечный: цель — не отрисовать приложение, а дойти до конца
загрузки без исключения.
"""
import io
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dukpy

import bundle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

SHIM = """
var __mod = {};
var window = this;
var localStorage = {
  _d: {},
  getItem: function (k) { return this._d[k] === undefined ? null : this._d[k]; },
  setItem: function (k, v) { this._d[k] = String(v); },
  removeItem: function (k) { delete this._d[k]; },
};
var __listeners = [];
function __el() {
  return {
    innerHTML: '', textContent: '', value: '', hidden: false, disabled: false,
    dataset: {}, style: { setProperty: function () {} },
    classList: { add: function () {}, remove: function () {},
                 toggle: function () {}, contains: function () { return false; } },
    appendChild: function () {}, append: function () {}, remove: function () {},
    addEventListener: function () {}, removeEventListener: function () {},
    querySelector: function () { return __el(); },
    querySelectorAll: function () { return []; },
    closest: function () { return null; },
    insertAdjacentHTML: function () {},
    replaceWith: function () {}, scrollIntoView: function () {},
    setAttribute: function () {}, focus: function () {},
    getContext: function () { return null; },
    content: { firstElementChild: null },
  };
}
var document = {
  documentElement: __el(),
  body: __el(),
  createElement: function () { return __el(); },
  getElementById: function () { return __el(); },
  querySelector: function () { return __el(); },
  querySelectorAll: function () { return []; },
  addEventListener: function (n, f) { __listeners.push(n); },
  visibilityState: 'visible',
};
window.addEventListener = function () {};
window.scrollTo = function () {};
window.open = function () {};
window.confirm = function () { return true; };
window.alert = function () {};
var history = { pushState: function () {}, back: function () {} };
var location = { search: '', reload: function () {} };
var navigator = { userAgent: 'test' };
// Таймер выполняет обещанное сразу: движку некуда ждать, а проверкам
// нужен результат. Задержки в коде (подстраховочный запрос к miet.ru,
// откладывание отрисовки) от этого не ломаются — они про порядок, а не
// про часы.
var setTimeout = function (f) {
  if (typeof f === 'function') { try { f(); } catch (e) {} }
  return 0;
};
var clearTimeout = function () {};
var requestAnimationFrame = function (f) { return 0; };
var IntersectionObserver = function () {
  return { observe: function () {}, unobserve: function () {} };
};
var AbortController = function () { this.signal = {}; this.abort = function () {}; };
var fetch = function () {
  return { then: function () { return this; }, catch: function () { return this; },
           finally: function () { return this; } };
};
var Telegram = undefined;
var console = { log: function () {}, warn: function () {}, error: function () {} };
"""


def main() -> int:
    files = bundle.modules()
    # Тот же сборщик, что уезжает на Pages: проверки гоняют ровно то,
    # что увидит человек, а не похожую сборку.
    code = bundle.build(SHIM) + "\n'ok';"
    # Сборку кладём во временную папку: она нужна только чтобы посмотреть
    # на строку из сообщения об ошибке, и в репозитории ей не место.
    dump = os.path.join(tempfile.gettempdir(), "miet-bundle.js")
    io.open(dump, "w", encoding="utf-8").write(code)
    try:
        dukpy.evaljs(code)
    except Exception as e:                              # noqa: BLE001
        print("ОШИБКА ПРИ ЗАГРУЗКЕ:")
        print(str(e)[:1500])
        print()
        print("собранный скрипт лежит в " + dump
              + " — номер строки из сообщения указывает на него")
        return 1
    print(f"все {len(files)} модулей загрузились без ошибок")
    return check_logic(code)


# Чистые функции, которые ломаются молча: неверный значок или «6 дн.
# назад» вместо «вчера» не роняют приложение, их видно только глазами —
# а глаз тут ни у кого нет.
CASES = [
    ("значок физики", "subjectLook('Физика. Механика').glyph", "atom"),
    ("значок матанализа", "subjectLook('Математический анализ').glyph", "sigma"),
    ("значок истории", "subjectLook('История России').glyph", "column"),
    ("значок языка", "subjectLook('Иностранный язык').glyph", "languages"),
    ("значок информатики", "subjectLook('Информатика').glyph", "code"),

    # Частное правило обязано стоять выше общего: в «начертательной
    # геометрии» есть «геометр», и без порядка она уехала бы к
    # математике, а «теория вероятностей» — к ней же по слову «теор».
    ("начерталка — это черчение",
     "subjectLook('Начертательная геометрия').glyph", "draft"),
    ("вероятность — не алгебра",
     "subjectLook('Теория вероятностей и математическая статистика').glyph",
     "stats"),
    ("схемотехника своя", "subjectLook('Схемотехника').glyph", "chip"),

    # Три ловушки, пойманные на живом расписании МИЭТ, а не придуманные.
    # Каждая выглядела правдоподобно и давала не тот значок.
    ("виды спорта — это физкультура, а не психология",
     "subjectLook('Индивидуальные виды спорта / Командные виды спорта').glyph",
     "dumbbell"),
    ("«управления» — не «право»",
     "subjectLook('Основы управления проектами').glyph", "coins"),
    ("теория информации — про код",
     "subjectLook('Основы теории информации и кодирования').glyph", "code"),
    ("ТФКП — математика",
     "subjectLook('Теория функций комплексной переменной').glyph", "sigma"),
    ("БЖД своя", "subjectLook('Безопасность жизнедеятельности').glyph",
     "shieldc"),
    # Цвет незнакомого предмета не случайный: при каждом открытии он
    # обязан быть тем же, иначе цвет ничего не значит.
    ("незнакомый предмет — тот же цвет",
     "String(subjectLook('Кристаллография').tone === subjectLook('Кристаллография').tone"
     " && subjectLook('Кристаллография').glyph === 'bookOpen')", "true"),
    # Значок рисуется телом из таблицы цветов, а не заглушкой.
    ("у физики есть цветное тело", "String(hasColor('atom'))", "true"),
    ("плашка несёт цвет предмета",
     "String(subjectBadge('Физика').indexOf('tone-4') > 0)", "true"),
    ("незнакомый предмет получает свой",
     "subjectLook('Начерталка').glyph", "bookOpen"),
    ("цвет предмета постоянный",
     "String(subjectLook('Начерталка').tone === subjectLook('Начерталка').tone)",
     "true"),
    # Откат на прямой адрес. Вне браузера (и на Pages) база и так прямая,
    # значит уходить некуда — это и проверяем: второй раз не дёргаемся.
    ("адрес сервера известен",
     "String(apiBase().indexOf('miet-bot-rouk.amvera.io') > 0)", "true"),
    ("с прямого адреса уходить некуда", "String(fallBackToHome())", "false"),
    ("и он не испортился", "String(apiBase().indexOf('https://') === 0)", "true"),
    # Обновление страницы на свежую сборку: метка ставится, а параметры
    # входа (группа, startapp) обязаны пережить перезагрузку.
    ("метка попадает в адрес",
     "String(freshUrl('https://m.ru/?group=%D0%9F-13', 'abc').indexOf('v=abc') > 0)",
     "true"),
    ("и группа не теряется",
     "String(freshUrl('https://m.ru/?group=X', 'abc').indexOf('group=X') > 0)",
     "true"),
    ("старая метка заменяется, а не копится",
     "freshUrl('https://m.ru/?v=old', 'new')", "https://m.ru/?v=new"),
    ("пустая дата не ломает разбор", "newsDate('').text", ""),
    ("кривая дата отдаётся как есть", "newsDate('позавчера').text", "позавчера"),
    ("пункт перечня распознан", "String(NUMBERED.test('1. Теории'))", "true"),
    ("буквенный пункт распознан", "String(NUMBERED.test('А) Княжение'))", "true"),
    ("обычный абзац не пункт",
     "String(NUMBERED.test('Подготовить доклады'))", "false"),
    ("ссылка становится ссылкой",
     "String(linkify('см. https://a.ru/x').indexOf('data-url=') > 0)", "true"),
    ("разметка в тексте экранирована",
     "String(linkify('<b>тут</b>').indexOf('&lt;b&gt;') >= 0)", "true"),
    ("вложение-PDF узнано",
     "fileLook('Задание', 'https://orioks.miet.ru/x/dz.pdf').label", "PDF"),
    ("вложение-документ узнано",
     "fileLook('Деловое письмо.docx', '').label", "DOC"),
    ("ссылка на ресурс узнана",
     "fileLook('Ссылки на лекции', 'https://vk.com/x').label", "Ссылка"),
    ("незнакомое вложение без подписи",
     "fileLook('Материал', '/storage/d/1/abc').label", ""),

    # 1 сентября 2026 — вторник. Вторая учебная неделя обязана начаться
    # 7-го, как её считает сам ОРИОКС, а не 8-го: иначе лаба, которая
    # завтра, показывалась сроком «14 сентября».
    ("вторая неделя начинается с понедельника",
     "weekMonday(new Date(2026, 8, 1), 2).getDate()", "7"),
    ("первая неделя — понедельник до 1 сентября",
     "weekMonday(new Date(2026, 8, 1), 1).getDate()", "31"),
    ("без номера недели даты нет",
     "String(weekMonday(new Date(2026, 8, 1), 0))", "null"),

    ("предмет узнаётся по длинным словам",
     "subjectKey('Физика. Механика. Термодинамика')", "физика механика"),
    ("предмет ОРИОКС и расписания сходится",
     "String(subjectKey('Линейная алгебра и аналитическая геометрия')"
     " === subjectKey('Линейная алгебра, аналитическая геометрия'))", "true"),

    # Лабораторную ищем среди лабораторных, а не среди любых пар этого
    # предмета: лекция по физике в тот же день сроком сдачи не является.
    ("день лабораторной берётся из расписания",
     "lessonDay(SCHED, new Date(2026, 8, 1),"
     " { week: 2, type: 'Лабораторная работа' }, 'Физика. Механика', 0)"
     ".date.getDate()", "10"),
    ("вид пары совпал с видом работы",
     "String(lessonDay(SCHED, new Date(2026, 8, 1),"
     " { week: 2, type: 'Лабораторная работа' }, 'Физика. Механика', 0)"
     ".exact)", "true"),
    ("без своей пары берём любую по предмету",
     "lessonDay(SCHED, new Date(2026, 8, 1),"
     " { week: 2, type: 'Реферат' }, 'Физика. Механика', 0).date.getDate()",
     "11"),
    ("чужого предмета в расписании нет",
     "String(lessonDay(SCHED, new Date(2026, 8, 1),"
     " { week: 2, type: 'Лабораторная работа' }, 'Философия', 0))", "null"),

    # Расписание приходит двумя путями, и имя преподавателя в них
    # называется по-разному: рисуем то, что пришло.
    ("короткое имя берётся первым",
     "__scr.teacherOf({ teacherShort: 'Иванов И.И.', teacher: 'Иванов Иван' })",
     "Иванов И.И."),
    ("без короткого берём полное",
     "__scr.teacherOf({ teacher: 'Иванов Иван Иванович' })",
     "Иванов Иван Иванович"),
    ("без имени не рисуем ничего", "__scr.teacherOf({})", ""),
    ("и пустая запись не роняет", "__scr.teacherOf(null)", ""),

    # Окно между парами: тот же расчёт есть у бота, и расходиться им
    # нельзя — иначе в приложении окно есть, а в сообщении нет.
    ("окно найдено одно", "gapsOf(WITH_GAP).length", "1"),
    ("окно между второй и пятой",
     "gapsOf(WITH_GAP)[0].after + '-' + gapsOf(WITH_GAP)[0].before", "2-5"),
    ("пропущено две пары", "gapsOf(WITH_GAP)[0].pairs", "2"),
    ("длительность посчитана", "gapsOf(WITH_GAP)[0].minutes", "250"),
    ("подряд идущие пары окна не дают",
     "gapsOf(WITH_GAP.slice(0, 2)).length + gapsOf([]).length", "0"),
    ("окно называется по-человечески", "humanGap(250)", "4 ч 10 мин"),
    ("ровный час без минут", "humanGap(120)", "2 ч"),
    ("меньше часа — только минуты", "humanGap(45)", "45 мин"),
    ("нулевое окно не называется никак", "humanGap(0)", ""),

    # Один и тот же запрос не должен уходить дважды: приложение
    # спрашивает расписание при старте, экран — когда рисует.
    ("два запроса подряд дают одно обещание",
     "String(_sc.fetchSchedule('Р-1') === _sc.fetchSchedule('Р-1'))", "true"),

    # Расписание берётся у того, кто ответил: бот быстрее и легче, но
    # молчащий бот не должен оставлять человека без пар.
    ("живы оба — берём ответ бота", "__botWon.semestr", "от бота"),
    ("бот молчит — берём с сайта", "__siteWon.semestr", "с сайта"),
    ("молчат оба — честная ошибка",
     "String(__bothDead.indexOf('Расписание не пришло') === 0)", "true"),

    # Отказ сети не должен превращаться в «данных нет»: расписание
    # меняется раз в семестр, и вчерашняя копия — то же расписание.
    ("копия отдаётся, когда сеть молчит", "__stale.lessons.length", "2"),
    ("и помечена как сохранённая", "String(__stale.stale)", "true"),
    ("без копии — человеческое сообщение",
     "String(__failed.indexOf('Расписание') === 0 || __failed.indexOf('Нет сети') === 0)",
     "true"),
    ("и в нём названа причина", "String(__failed.indexOf('нет сети') > 0)", "true"),

    # День без пар — обычное дело: у ИКТ-12 такой четверг всегда. Он
    # обязан выглядеть свободным днём, а не отказом загрузки.
    ("пустой день отдаёт пустой список",
     "slotsOf(NO_THURSDAY, 0, 4).length", "0"),
    ("день с парами отдаёт пары", "slotsOf(NO_THURSDAY, 0, 1).length", "1"),
    ("счётчик дней знает про пустой четверг",
     "String(dayCounts(NO_THURSDAY, 0)[4] || 0)", "0"),
    ("счётчик дней знает про занятый понедельник",
     "String(dayCounts(NO_THURSDAY, 0)[1])", "1"),
    ("в пустой день ничего не идёт и не падает",
     "String(nowState(NO_THURSDAY, 0, new Date(2026, 8, 10, 12, 0)).current)",
     "null"),
    ("и следующей пары в нём тоже нет",
     "String(nowState(NO_THURSDAY, 0, new Date(2026, 8, 10, 12, 0)).next)",
     "null"),

    # Картинка поста занимает место по своим пропорциям: единое
    # соотношение резало пополам скриншоты расписания.
    ("размеры читаются из имени",
     "mediaSize('abc-1200x800.jpg').w", "1200"),
    ("у старого имени размеров нет",
     "String(mediaSize('abc.jpg'))", "null"),
    ("пропорции попадают в разметку",
     "String(mediaTag('abc-1200x800.jpg').indexOf('aspect-ratio:1200/800') > 0)",
     "true"),
    ("высокой картинке отводится своё место",
     "String(mediaTag('abc-800x1600.jpg').indexOf('aspect-ratio:4/5') > 0)",
     "true"),
    ("высокая вписывается целиком",
     "String(mediaTag('abc-800x1600.jpg').indexOf('tall') > 0)", "true"),
    ("без размеров картинка помечена",
     "String(mediaTag('abc.jpg').indexOf('unsized') > 0)", "true"),

    # Иллюстрации: сцена обязана быть настоящим svg, а незнакомое имя —
    # не пустотой на пол-экрана, а хоть чем-то.
    ("сцена рисуется", "String(art('free').indexOf('<svg') === 0)", "true"),
    ("сцена знает свой размер",
     "String(art('rest', 64).indexOf('width=\"64\"') > 0)", "true"),
    ("незнакомая сцена не оставляет дыру",
     "String(art('такой-нет').length > 100)", "true"),
    ("пустое состояние подписано",
     "String(artState('free', 'Пар нет').indexOf('Пар нет') > 0)", "true"),
    ("подпись экранирована",
     "String(artState('free', '<b>x</b>').indexOf('&lt;b&gt;') > 0)", "true"),

    # Разбор ведомости общий у экрана заданий и главной: если он начнёт
    # считать делами посещаемость, это увидят оба сразу.
    ("ведомость разворачивается целиком", "PLAN.length", "4"),
    ("в делах только настоящее задание", "TODO.length", "1"),
    ("сданное делом не считается",
     "String(TODO.every(function (t) { return !t.done; }))", "true"),
    ("формальности и сессия отсеяны", "TODO[0].name", "ЛР.2"),
    ("у дела есть срок и предмет",
     "String(TODO[0].due instanceof Date && TODO[0].subject.length > 0)",
     "true"),

    # Розыгрыш: склонение и подписи дней. И то, и другое стоит рядом с
    # числом приглашённых, где «5 человека» бросается в глаза сразу.
    ("один человек", "plural(1, 'человек', 'человека', 'человек')", "человек"),
    ("двое", "plural(2, 'человек', 'человека', 'человек')", "человека"),
    ("пятеро", "plural(5, 'человек', 'человека', 'человек')", "человек"),
    ("одиннадцать — исключение",
     "plural(11, 'день', 'дня', 'дней')", "дней"),
    ("двадцать один день", "plural(21, 'день', 'дня', 'дней')", "день"),
    ("подпись дня недели", "dayLabel('2026-09-16')", "ср"),

    # Две группы: что считать общей парой и что — общим окном. Ошибка
    # здесь тихая — экран покажет число, просто не то.
    ("потоковая лекция — общая пара",
     "String(sameLesson('Физика. Оптика', 'Физика.Оптика'))", "true"),
    ("разные предметы в одном слоте — не вместе",
     "String(sameLesson('Матанализ', 'Базы данных'))", "false"),
    ("пустой предмет ничему не равен",
     "String(sameLesson('', ''))", "false"),
    ("общая пара засчитана", "String(CMP.together)", "1"),
    ("у каждого своё — тоже", "String(CMP.both)", "1"),
    ("окно считается только внутри дня", "String(CMP.free)", "1"),
    ("слоты до начала дня в разбор не идут", "String(CMP.rows.length)", "4"),

    # Свободные аудитории: слот по часам и подпись «до какого времени».
    ("во время пары показываем её", "String(pairNow(new Date(2026, 8, 16, 9, 30)))", "1"),
    ("в перерыв — следующую", "String(pairNow(new Date(2026, 8, 16, 10, 35)))", "2"),
    ("поздно вечером — первую", "String(pairNow(new Date(2026, 8, 16, 23, 30)))", "1"),
    ("свободна до конца дня", "untilText({ until_pair: null })", "до конца дня"),
    ("свободна до времени",
     "untilText({ until_pair: 4, until_time: '14:20' })", "до 14:20"),
    # Фильтр по первой цифре заменил заголовки «3xxx»: что эта цифра
    # значит в нумерации МИЭТ, нигде не написано, и подпись обещала
    # смысл, которого нет.
    # Длинные тексты вынесены в отдельный файл: карточка берёт их
    # оттуда, но обязана уметь и старый формат — в запасном app.json
    # текст лежит внутри записи.
    ("текст из самой записи",
     "textOf('news', { id: '1', text: 'внутри' })", "внутри"),
    ("пустая запись не роняет", "String(textOf('news', null) === '')", "true"),
    ("нет текста — пустая строка",
     "String(textOf('news', { id: 'нетакого' }) === '')", "true"),

    ("номер относится к своей цифре", "blockOf('3105')", "3"),
    ("нечисловое имя — в «прочие»", "blockOf('Спорткомплекс')", "#"),
    ("фильтры собраны без повторов",
     "blocksOf([{name:'3105'},{name:'4202'},{name:'3118'}]).join(',')", "3,4"),
    ("«прочие» уходят в конец",
     "blocksOf([{name:'Спорткомплекс'},{name:'3105'}]).join(',')", "3,#"),
    ("кривая дата подписи не даёт", "String(dayLabel('') === '')", "true"),
    # Названия недель — слово в слово как у miet.ru, по ним студенты и
    # сверяются с официальным расписанием; счёт цикла идёт по кругу.
    ("неделя 0 — 1-й числитель", "weekName(0)", "1-й числитель"),
    ("неделя 1 — 1-й знаменатель", "weekName(1)", "1-й знаменатель"),
    ("неделя 2 — 2-й числитель", "weekName(2)", "2-й числитель"),
    ("неделя 3 — 2-й знаменатель", "weekName(3)", "2-й знаменатель"),
    ("сдвиг за конец цикла — по кругу", "weekName(3 + 2)", "1-й знаменатель"),
    # Успеваемость. Главная ловушка — `max_grade` дисциплины: это максимум
    # по оценённому, а не за семестр; сумма берётся по всем точкам.
    ("семестр — сумма всех точек", "standing(INF).max", "100"),
    ("набрано — из ОРИОКС", "standing(INF).got", "10"),
    ("процент — от выставленного", "standing(INF).pct", "100"),
    ("полоса — от семестра", "standing(INF).share", "10"),
    ("до тройки не хватает", "standing(INF).next.label + ' ' + standing(INF).next.left",
     "Удовлетворительно 40"),
    ("у зачёта одна граница", "standing(PASS).now + ' ' + standing(PASS).next", "Зачтено null"),
    ("экзамен: текущая оценка", "standing(EXAM).now", "Хорошо"),
    ("экзамен: до пятёрки", "standing(EXAM).next.left", "16"),
    ("без оценок процента нет", "standing(NONE).pct", "null"),
    ("дробный балл с запятой", "gnum(7.5)", "7,5"),
    ("целый балл без нулей", "gnum(8)", "8"),
    ("выставлено сегодня", "agoLabel(daysAgo(0), NOW)", "сегодня"),
    ("выставлено вчера", "agoLabel(daysAgo(1), NOW)", "вчера"),
    ("три дня назад", "agoLabel(daysAgo(3), NOW)", "3 дня назад"),
    ("пять дней назад", "agoLabel(daysAgo(5), NOW)", "5 дней назад"),
    ("двадцать один день", "agoLabel(daysAgo(21), NOW)", "21 день назад"),
    ("кривое время — пусто", "agoLabel('', NOW)", ""),
    ("новые баллы — только выставленные",
     "recentGrades({disciplines:[INF]}, {'1:ЛР.1': daysAgo(1), '1:ЛР.2': daysAgo(0)})"
     ".map(function (r) { return r.name; }).join(',')", "ЛР.1"),
    ("свежие сверху",
     "recentGrades({disciplines:[{name:'А', events:[{key:'a', done:true},{key:'b', done:true}]}]},"
     " {a: daysAgo(3), b: daysAgo(1)}).map(function (r) { return r.key; }).join(',')", "b,a"),
]

# Бот подписывает недели тем же словарём (bot/schedule_api.WEEK_NAMES):
# разойдись они — в сообщении бота и в приложении была бы разная неделя.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot.schedule_api import WEEK_NAMES as _BOT_WEEKS  # noqa: E402
CASES += [(f"неделя {i} у бота та же", f"weekName({i})", n)
          for i, n in enumerate(_BOT_WEEKS)]


# Модули в сборке завёрнуты, глобальных имён нет: достаём нужное из
# таблицы экспортов и раскладываем по коротким именам.
PRELUDE = """
var _t = __mod['js/screens/tasks.js'];
var subjectLook = _t.subjectLook, newsDate = _t.newsDate,
    linkify = _t.linkify, NUMBERED = _t.NUMBERED, fileLook = _t.fileLook,
    weekMonday = _t.weekMonday, subjectKey = _t.subjectKey,
    lessonDay = _t.lessonDay, flatten = _t.flatten, pendingOf = _t.pendingOf,
    standing = _t.standing, agoLabel = _t.agoLabel,
    recentGrades = _t.recentGrades, gnum = _t.num;

// Предмет, как его видит живой ОРИОКС после первой лабораторной: у
// дисциплины «10 из 10», хотя за семестр можно набрать 100.
var INF = { name: 'Информатика', control_form: 'Дифференцированный зачёт',
  current_grade: 10, max_grade: 10, events: [
    { key: '1:ЛР.1', name: 'ЛР.1', done: true, grade: 10, max_grade: 10 },
    { key: '1:ЛР.2', name: 'ЛР.2', done: false, grade: null, max_grade: 90 }] };
var PASS = { control_form: 'Зачёт', current_grade: 55, semester_max: 100, events: [] };
var EXAM = { control_form: 'Экзамен', current_grade: 70, semester_max: 100, events: [] };
var NONE = { control_form: 'Экзамен', current_grade: 0, max_grade: 0,
  events: [{ done: false, max_grade: 100 }] };
var NOW = new Date(2026, 8, 24, 15, 0);
var utcOf = function (d) { return d.toISOString().slice(0, 19).replace('T', ' '); };
var daysAgo = function (n) { var d = new Date(NOW); d.setDate(d.getDate() - n); return utcOf(d); };
// Адрес серверной части: откуда спрашиваем данные и куда уходим, если
// раздатчик страницы сервером не оказался.
var _cfg = __mod['js/config.js'];
var apiBase = _cfg.apiBase, fallBackToHome = _cfg.fallBackToHome;

// Адрес той же страницы с новой меткой выкладки.
var _fr = __mod['js/fresh.js'];
var freshUrl = _fr.freshUrl;

var _a = __mod['js/art.js'];
var art = _a.art, artState = _a.artState;
var _f = __mod['js/screens/feed.js'];
var mediaSize = _f.mediaSize, mediaTag = _f.mediaTag;

var _cm = __mod['js/screens/compare.js'];
var sameLesson = _cm.sameLesson, compareDay = _cm.compareDay;
var _fr2 = __mod['js/screens/free.js'];
var pairNow = _fr2.pairNow, untilText = _fr2.untilText,
    blockOf = _fr2.blockOf, blocksOf = _fr2.blocksOf;

var _st = __mod['js/store.js'];
var textOf = _st.textOf;

var _sj = __mod['js/subjects.js'];
var hasColor = _sj.hasColor, subjectBadge = _sj.subjectBadge;

var _rf = __mod['js/screens/raffle.js'];
var plural = _rf.plural, dayLabel = _rf.dayLabel;

var __scr = __mod['js/screens/schedule.js'];
var _sc = __mod['js/schedule.js'];
var gapsOf = _sc.gapsOf, humanGap = _sc.humanGap, weekName = _sc.weekName;

// День с дыркой в номерах пар: после второй сразу пятая.
var WITH_GAP = [
  { pair: 1, from: '09:00', to: '10:20' },
  { pair: 2, from: '10:30', to: '11:50' },
  { pair: 5, from: '16:00', to: '17:20' }
];
var slotsOf = _sc.slotsOf, dayCounts = _sc.dayCounts, nowState = _sc.nowState;

// Два источника наперегонки: бот и сам сайт института. Проверяем, что
// берётся ответивший, а молчание одного не оставляет человека без
// расписания.
//
// Заглушка сети одна на все случаи и решает по имени группы: обещания
// разворачиваются не сразу, и три подменённых по очереди `fetch`
// перепутались бы между собой.
var __botWon = null, __siteWon = null, __bothDead = '', __stale = null,
    __failed = '';
(function () {
  var BOT = { ready: true, semestr: 'от бота', times: [], lessons: [{ day: 1 }] };
  var SITE = { Semestr: 'с сайта', Times: [], Data: [] };
  var ok = function (body) {
    return Promise.resolve({ ok: true, status: 200,
      json: function () { return Promise.resolve(body); } });
  };
  var no = function (why) { return Promise.reject(new Error(why)); };

  fetch = function (url) {
    var u = String(url);
    var bot = u.indexOf('/api/schedule') >= 0;
    if (u.indexOf('%D0%A0-1') >= 0 || u.indexOf('Р-1') >= 0) {
      return ok(bot ? BOT : SITE);            // живы оба
    }
    if (u.indexOf('%D0%A0-2') >= 0 || u.indexOf('Р-2') >= 0) {
      return bot ? no('бот молчит') : ok(SITE);  // бот молчит
    }
    return no('нет сети');                    // всё остальное — тишина
  };

  var copy = { at: 0, data: { semestr: 'Осенний семестр 2026/2027', times: [],
    lessons: [{ week: 0, day: 1 }, { week: 0, day: 2 }] } };
  localStorage.setItem('miet-sched:Г-1', JSON.stringify(copy));

  var keep = function (put) {
    return function (v) { put(v); };
  };
  _sc.fetchSchedule('Р-1', { force: true }).then(
    keep(function (v) { __botWon = v; }), function () {});
  _sc.fetchSchedule('Р-2', { force: true }).then(
    keep(function (v) { __siteWon = v; }), function () {});
  _sc.fetchSchedule('Р-3', { force: true }).then(
    function () {}, function (e) { __bothDead = e.message; });
  // Копия есть — её и покажем, вместо ошибки.
  _sc.fetchSchedule('Г-1').then(
    keep(function (v) { __stale = v; }), function () {});
  _sc.fetchSchedule('Г-2').then(
    function () {}, function (e) { __failed = e.message; });
})();

// Расписание группы, у которой в четверг пар нет вовсе (так живёт
// ИКТ-12): пустой день обязан оставаться пустым днём, а не поломкой.
var NO_THURSDAY = { semestr: 'Осенний семестр 2026/2027', times: [], lessons: [
  { week: 0, day: 1, pair: 1, from: '09:00', to: '10:20',
    subject: 'Физика', kind: 'Лекция', kindCls: 'lek', flags: [], room: '1201' },
  { week: 0, day: 5, pair: 2, from: '10:30', to: '11:50',
    subject: 'Физика', kind: 'Лабораторная', kindCls: 'lab', flags: [], room: '3229' }
] };

var SCHED = { semestr: 'Осенний семестр 2026/2027', lessons: [
  { week: 1, day: 4, pair: 3, subject: 'Физика. Механика',
    kindCls: 'lab', from: '12:00', room: '3229' },
  { week: 1, day: 5, pair: 2, subject: 'Физика. Механика',
    kindCls: 'lek', from: '10:30', room: '1201' }
] };

// Ведомость в том виде, в каком её отдаёт сервер: задание, сданное
// задание, экзамен и формальность. Из четырёх записей делом является
// ровно одна.
var VEDOMOST = { disciplines: [{ name: 'Физика. Механика', events: [
  { name: 'ЛР.2', type: 'Лабораторная работа', week: 10, max_grade: 10,
    grade: null, done: false, task: true, session: false },
  { name: 'ЛР.1', type: 'Лабораторная работа', week: 2, max_grade: 10,
    grade: 8, done: true, task: true, session: false },
  { name: 'Экзамен', type: 'Экзамен', week: 17, max_grade: 30,
    done: false, task: false, session: true },
  { name: 'А/П', type: 'Активность/Посещаемость', week: 8, max_grade: 24,
    done: false, task: false, session: false }
] }] };

// День двух групп: первая пара общая (поток), вторая у каждого своя,
// третья пустая у обоих (окно), четвёртая только у одного.
var CMP = compareDay(
  [{ pair: 1, subject: 'Физика', from: '9:00' },
   { pair: 2, subject: 'Матанализ', from: '10:40' },
   { pair: 4, subject: 'Базы данных', from: '14:20' }],
  [{ pair: 1, subject: 'Физика', from: '9:00' },
   { pair: 2, subject: 'Химия', from: '10:40' }]);

var PLAN = flatten(VEDOMOST, SCHED, new Date(2026, 8, 1), 0);
var TODO = pendingOf(PLAN);
"""


def check_logic(bundle: str) -> int:
    """
    Гоняет чистые функции клиента на живом движке.

    Контекст один на все проверки, а не по одному на каждую: часть
    подготовки — обещания (загрузка расписания с подменённой сетью), а
    они разрешаются не сразу. Между подготовкой и проверками очередь
    прокручивается вхолостую — иначе обещание так и осталось бы
    висящим, а проверка сравнивала бы пустоту.
    """
    try:
        js = dukpy.JSInterpreter()
        js.evaljs(bundle + PRELUDE + "\n'готово';")
        for _ in range(50):
            js.evaljs("0;")
    except Exception as e:                              # noqa: BLE001
        print(f"  ✗ подготовка не выполнилась: {str(e)[:300]}")
        return 1

    bad = 0
    for name, expr, want in CASES:
        try:
            got = js.evaljs("String(" + expr + ");")
        except Exception as e:                          # noqa: BLE001
            print(f"  ✗ {name}: {str(e)[:200]}")
            bad += 1
            continue
        if str(got) != want:
            print(f"  ✗ {name}: получили {got!r}, ждали {want!r}")
            bad += 1
    if bad:
        print(f"логика клиента: провалено {bad} из {len(CASES)}")
        return 1
    print(f"логика клиента: {len(CASES)} проверок сошлись")
    return 0


if __name__ == "__main__":
    sys.exit(main())
