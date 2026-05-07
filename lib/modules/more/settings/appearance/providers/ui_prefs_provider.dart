import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive/hive.dart';

const _kBox = 'ui_prefs';

Box? get _box => Hive.isBoxOpen(_kBox) ? Hive.box(_kBox) : null;

// ── Carousel Style ────────────────────────────────────────────────────────────
// 0 = classic (cards scale), 1 = cinematic (full width), 2 = compact

class CarouselStyleNotifier extends Notifier<int> {
  @override
  int build() => (_box?.get('carousel_style', defaultValue: 0) as num?)?.toInt() ?? 0;

  void set(int v) {
    _box?.put('carousel_style', v);
    state = v;
  }
}

final carouselStyleProvider = NotifierProvider<CarouselStyleNotifier, int>(
  CarouselStyleNotifier.new,
);

const carouselStyleLabels = ['Classic', 'Cinematic', 'Compact'];

// ── Card Style ────────────────────────────────────────────────────────────────
// 0 = standard, 1 = modern (rounded), 2 = blur

class CardStyleNotifier extends Notifier<int> {
  @override
  int build() => (_box?.get('card_style', defaultValue: 0) as num?)?.toInt() ?? 0;

  void set(int v) {
    _box?.put('card_style', v);
    state = v;
  }
}

final cardStyleProvider = NotifierProvider<CardStyleNotifier, int>(
  CardStyleNotifier.new,
);

const cardStyleLabels = ['Standard', 'Modern', 'Blur'];

// ── Glow Effects ──────────────────────────────────────────────────────────────

class GlowEffectsNotifier extends Notifier<bool> {
  @override
  bool build() => _box?.get('glow_effects', defaultValue: true) as bool? ?? true;

  void set(bool v) {
    _box?.put('glow_effects', v);
    state = v;
  }
}

final glowEffectsProvider = NotifierProvider<GlowEffectsNotifier, bool>(
  GlowEffectsNotifier.new,
);

// ── Carousel Synopsis ─────────────────────────────────────────────────────────

class CarouselSynopsisNotifier extends Notifier<bool> {
  @override
  bool build() => _box?.get('carousel_synopsis', defaultValue: true) as bool? ?? true;

  void set(bool v) {
    _box?.put('carousel_synopsis', v);
    state = v;
  }
}

final carouselSynopsisProvider = NotifierProvider<CarouselSynopsisNotifier, bool>(
  CarouselSynopsisNotifier.new,
);

// ── Detail Ken Burns ──────────────────────────────────────────────────────────

class KenBurnsNotifier extends Notifier<bool> {
  @override
  bool build() => _box?.get('ken_burns', defaultValue: true) as bool? ?? true;

  void set(bool v) {
    _box?.put('ken_burns', v);
    state = v;
  }
}

final kenBurnsProvider = NotifierProvider<KenBurnsNotifier, bool>(
  KenBurnsNotifier.new,
);
