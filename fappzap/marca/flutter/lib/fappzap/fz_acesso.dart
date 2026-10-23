// FappZap Acesso (23/10/2026) — o que a Fapp acrescenta ao RustDesk do lado de QUEM CONECTA (o técnico).
// Mora num arquivo próprio para o código do RustDesk só ganhar ganchos de uma linha (fappzap/aplicar-marca.py,
// passos 3i e 3j). Nada aqui roda no computador acessado.
import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_hbb/common.dart';
import 'package:flutter_hbb/consts.dart';
import 'package:flutter_hbb/models/model.dart';
import 'package:flutter_hbb/models/platform_model.dart';

// ── TROCAR DE TELA PELA BORDA ─────────────────────────────────────────────────────────────────────────────
// Vendo UM monitor de um cliente que tem vários, o mouse parado na borda onde o cliente tem outro monitor
// encostado troca a tela para ele, e o cursor entra pela borda oposta — como o mouse passa de um monitor para
// o outro lá. Só depois de [_espera] parado na borda: passar rente não troca. Sair da janela cancela (quem
// leva o mouse para outro programa daqui não é puxado de volta). Em "Todas as telas", em janelas separadas,
// em tamanho original (com barra de rolagem) ou com botão apertado (arrastando), nada muda.

/// Opção deste computador: "N" desliga. Vazio = ligada (padrão de fábrica).
const kFzOpcaoBorda = 'fz-trocar-tela-borda';
const _espera = Duration(milliseconds: 300);

bool fzBordaLigada() => bind.mainGetLocalOption(key: kFzOpcaoBorda) != 'N';

/// Gancho do leaveView: o mouse saiu da imagem (foi para outro programa daqui) — não troca de tela.
void fzBordaSaiu(FFI ffi) => _esperas[ffi]?.cancelar();
Future<void> fzLigarBorda(bool ligar) =>
    bind.mainSetLocalOption(key: kFzOpcaoBorda, value: ligar ? '' : 'N');

class _EsperaDaBorda {
  Timer? timer;
  String lado = '';
  void cancelar() {
    timer?.cancel();
    timer = null;
    lado = '';
  }
}

final _esperas = Expando<_EsperaDaBorda>('fz-borda');

class _Vizinho {
  final int indice;
  final Rect rect;
  _Vizinho(this.indice, this.rect);
}

/// O retângulo de UM monitor, igual ao FfiModel._getDisplaysRect (sem a escala, exceto em Linux).
Rect _rectDoMonitor(FFI ffi, Display d) {
  final s = ffi.ffiModel.isPeerLinux ? d.scale : 1.0;
  return Rect.fromLTWH(d.x, d.y, (d.width.toDouble() ~/ s).toDouble(),
      (d.height.toDouble() ~/ s).toDouble());
}

/// O monitor do cliente encostado no [lado] do atual, na altura (ou coluna) do mouse.
_Vizinho? _vizinho(FFI ffi, PeerInfo pi, Rect atual, String lado, double x, double y) {
  const folga = 12.0; // escala diferente entre os monitores pode deixar uns pixels de vão
  for (var i = 0; i < pi.displays.length; i++) {
    if (i == pi.currentDisplay) continue;
    final r = _rectDoMonitor(ffi, pi.displays[i]);
    bool encosta;
    if (lado == 'dir') {
      encosta = (r.left - atual.right).abs() <= folga && y >= r.top && y < r.bottom;
    } else if (lado == 'esq') {
      encosta = (r.right - atual.left).abs() <= folga && y >= r.top && y < r.bottom;
    } else if (lado == 'baixo') {
      encosta = (r.top - atual.bottom).abs() <= folga && x >= r.left && x < r.right;
    } else {
      encosta = (r.bottom - atual.top).abs() <= folga && x >= r.left && x < r.right;
    }
    if (encosta) return _Vizinho(i, r);
  }
  return null;
}

/// Gancho do InputModel._handlePointerDevicePos: cada movimento do mouse sobre a imagem.
/// [x]/[y]: já na coordenada do computador acessado; [xLocal]/[yLocal]: na área da imagem daqui (lógica),
/// de tamanho [largura] x [altura]; [escala]: quanto 1 pixel de lá vale aqui.
void fzBordaMovimento(FFI ffi,
    {required double x,
    required double y,
    required Rect rect,
    required double escala,
    required double xLocal,
    required double yLocal,
    required double largura,
    required double altura,
    required bool saiu,
    required int botoes}) {
  final espera = _esperas[ffi] ??= _EsperaDaBorda();
  final pi = ffi.ffiModel.pi;
  if (saiu ||
      botoes != 0 ||
      pi.displays.length < 2 ||
      pi.currentDisplay == kAllDisplayValue ||
      ffi.ffiModel.viewOnly ||
      ffi.canvasModel.viewStyle.style == kRemoteViewStyleOriginal) {
    espera.cancelar();
    return;
  }
  // Uns 2 pixels DAQUI, em pixels de lá (com a imagem reduzida, 1 pixel daqui cobre vários de lá).
  final tol = escala > 0 ? max(2.0, 2.0 / escala) : 2.0;
  String lado = '';
  if (x >= rect.right - tol) {
    lado = 'dir';
  } else if (x <= rect.left + tol) {
    lado = 'esq';
  } else if (y >= rect.bottom - tol) {
    lado = 'baixo';
  } else if (y <= rect.top + tol) {
    lado = 'cima';
  }
  if (lado.isEmpty) {
    espera.cancelar();
    return;
  }
  if (lado == espera.lado && espera.timer != null) return; // já esperando nesta borda
  espera.cancelar();
  if (!fzBordaLigada()) return;
  final alvo = _vizinho(ffi, pi, rect, lado, x, y);
  if (alvo == null) return;
  espera.lado = lado;
  espera.timer = Timer(_espera, () {
    espera.timer = null;
    espera.lado = '';
    _trocar(ffi, pi, alvo, lado, x, y, xLocal, yLocal, largura, altura);
  });
}

void _trocar(FFI ffi, PeerInfo pi, _Vizinho alvo, String lado, double x, double y,
    double xLocal, double yLocal, double largura, double altura) {
  if (pi.currentDisplay == alvo.indice || pi.currentDisplay == kAllDisplayValue) return;
  openMonitorInTheSameTab(alvo.indice, ffi, pi, updateCursorPos: false);
  // O cursor de lá entra pela borda oposta, na mesma altura (ou coluna); o ponteiro daqui vai para a borda de
  // entrada da janela — senão o próximo movimento o jogaria na borda de SAÍDA do monitor novo.
  final r = alvo.rect;
  const margem = 8.0;
  double rx = x, ry = y, lx = xLocal, ly = yLocal;
  if (lado == 'dir') {
    rx = r.left + 4;
    ry = y.clamp(r.top, r.bottom - 1).toDouble();
    lx = margem;
  } else if (lado == 'esq') {
    rx = r.right - 5;
    ry = y.clamp(r.top, r.bottom - 1).toDouble();
    lx = largura - margem;
  } else if (lado == 'baixo') {
    ry = r.top + 4;
    rx = x.clamp(r.left, r.right - 1).toDouble();
    ly = margem;
  } else {
    ry = r.bottom - 5;
    rx = x.clamp(r.left, r.right - 1).toDouble();
    ly = altura - margem;
  }
  // Movimento comum: só x e y, como texto (o Rust lê um mapa de texto; modificador vale pela presença da chave).
  bind.sessionSendMouse(
      sessionId: ffi.sessionId,
      msg: json.encode({'x': '${rx.toInt()}', 'y': '${ry.toInt()}'}));
  // Windows e Linux posicionam o ponteiro em pixel; o Mac, em ponto (= a unidade lógica do Flutter).
  final dpr = isMacOS
      ? 1.0
      : (ui.PlatformDispatcher.instance.views.firstOrNull?.devicePixelRatio ?? 1.0);
  bind.mainMoveCursorBy(dx: ((lx - xLocal) * dpr).round(), dy: ((ly - yLocal) * dpr).round());
}

// ── ⚡ PASSOS RÁPIDOS ─────────────────────────────────────────────────────────────────────────────────────
// Atalhos do Windows do computador acessado, como no TeamViewer. Tudo pelo teclado (as mesmas funções do
// "Inserir Ctrl+Alt+Del"): Win+R, digita o comando e Enter. Nada roda por fora do teclado.

void fzPassosRapidos(FFI ffi) {
  final sid = ffi.sessionId;
  Future<void> tecla(String nome, {bool ctrl = false, bool shift = false, bool win = false}) =>
      bind.sessionInputKey(
          sessionId: sid,
          name: nome,
          down: false,
          press: true,
          alt: false,
          ctrl: ctrl,
          shift: shift,
          command: win);
  Future<void> executar(String comando) async {
    await tecla('VK_R', win: true);
    await Future.delayed(const Duration(milliseconds: 800)); // a caixa Executar abrir
    await bind.sessionInputString(sessionId: sid, value: comando);
    await Future.delayed(const Duration(milliseconds: 300));
    await tecla('VK_RETURN');
  }

  final passos = <String, Future<void> Function()>{
    'Task Manager': () => tecla('VK_ESCAPE', ctrl: true, shift: true),
    'Command prompt': () => executar('cmd'),
    'Control Panel': () => executar('control'),
    'Computer Management': () => executar('compmgmt.msc'),
    'Device Manager': () => executar('devmgmt.msc'),
    'Programs and Features': () => executar('appwiz.cpl'),
    'System': () => executar('ms-settings:about'),
    'Windows Update': () => executar('ms-settings:windowsupdate'),
  };
  ffi.dialogManager.show((setState, close, context) {
    return CustomAlertDialog(
      title: Text(translate('Quick steps')),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: passos.entries
            .map((p) => TextButton(
                  style: TextButton.styleFrom(alignment: Alignment.centerLeft),
                  onPressed: () {
                    close();
                    p.value();
                  },
                  child: Text(translate(p.key)),
                ))
            .toList(),
      ),
      actions: [dialogButton('Close', onPressed: close, isOutline: true)],
      onCancel: close,
    );
  });
}
