import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AnimePlayerView extends ConsumerWidget {
  final int episodeId;
  const AnimePlayerView({super.key, required this.episodeId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return const Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.videocam_off, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'Video playback is not supported on web',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}

class AnimeStreamPage extends ConsumerWidget {
  final int episodeId;
  const AnimeStreamPage({super.key, required this.episodeId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return const Scaffold(
      body: Center(child: Text('Stream not supported on web')),
    );
  }
}

class VideoPrefs {
  final bool fit;
  final double brightness;
  final double volume;
  final double playbackSpeed;
  final bool skipButton;
  final bool autoPlay;
  const VideoPrefs({
    this.fit = false,
    this.brightness = 0,
    this.volume = 100,
    this.playbackSpeed = 1.0,
    this.skipButton = true,
    this.autoPlay = true,
  });
}

Widget seekIndicatorTextWidget(Duration duration, Duration currentPosition) {
  return const SizedBox.shrink();
}
