// Запасной вход в мини-приложение.
//
// Приложение и его API живут на одном российском адресе Amvera. У кого
// маршрут туда не доходит, тот теряет разом всё: и страницу, и
// расписание, и ленту. А маршрут не доходит чаще, чем кажется —
// Telegram в России у многих работает только через VPN, и трафик к нам
// приходит из-за рубежа. Выглядит это как ERR_CONNECTION_CLOSED:
// соединение закрылось, не дождавшись ответа.
//
// Воркер Cloudflare — второй путь к тому же серверу. Он отвечает со
// своих адресов, до которых дорога есть и из России, и из-под любого
// зарубежного узла, а сам ходит к нам. Проксируется ВСЁ, а не только
// страница: клиент спрашивает данные у того, кто его раздал
// (см. js/config.js), значит через воркер идут и API, и картинки.
//
// Основным входом он не становится намеренно: прямой путь короче, и
// у подавляющего большинства он работает. Воркер выдаётся поштучно —
// тому, кто сказал боту, что приложение не открывается.
//
// Выкладка: dash.cloudflare.com → Workers & Pages → Create → Worker,
// вставить этот файл целиком, Deploy. Полученный адрес вида
// https://<имя>.<аккаунт>.workers.dev положить в переменную MIRROR_URL
// в панели Amvera — без неё бот запасной вход не предлагает.

const ORIGIN = 'https://miet-bot-rouk.amvera.io';

// Сколько ждём наш сервер. Дольше держать незачем: контейнер
// перезапускается три минуты, и в это время он отвечает 503 сам.
const TIMEOUT = 25000;

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const target = ORIGIN + url.pathname + url.search;

    // Заголовки уходят как есть — в них подпись Telegram (X-Init-Data),
    // без неё сервер не узнает человека. Host убираем: его поставит
    // fetch, и поставит правильный, иначе Amvera не поймёт, чей это
    // запрос.
    const headers = new Headers(request.headers);
    headers.delete('host');
    headers.delete('cf-connecting-ip');

    const body = (request.method === 'GET' || request.method === 'HEAD')
      ? undefined : await request.arrayBuffer();

    let answer;
    try {
      answer = await fetch(target, {
        method: request.method,
        headers,
        body,
        redirect: 'manual',
        signal: AbortSignal.timeout(TIMEOUT),
      });
    } catch (e) {
      // Молчаливый обрыв здесь означает, что не дошли уже МЫ. Человеку
      // нужен текст, а не пустая вкладка: пусть знает, что чинить нечего
      // и надо просто повторить.
      return new Response(
        'Сервер приложения не ответил. Это бывает при выкладке — '
        + 'подожди пару минут и открой снова.\n\n' + e,
        { status: 502, headers: { 'content-type': 'text/plain; charset=utf-8' } });
    }

    // Ответ отдаём как пришёл, только помечаем — чтобы по заголовку было
    // видно, каким входом человек пришёл, когда он опять напишет «не
    // открывается».
    const out = new Headers(answer.headers);
    out.set('x-entry', 'mirror');
    return new Response(answer.body, {
      status: answer.status,
      statusText: answer.statusText,
      headers: out,
    });
  },
};
