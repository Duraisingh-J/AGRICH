import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../app/theme.dart';

class AnimatedGradientBackground extends StatefulWidget {
  const AnimatedGradientBackground({super.key, required this.child});

  final Widget child;

  @override
  State<AnimatedGradientBackground> createState() =>
      _AnimatedGradientBackgroundState();
}

class _AnimatedGradientBackgroundState extends State<AnimatedGradientBackground>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final base = Theme.of(context).scaffoldBackgroundColor;
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment(-1 + _controller.value, -1),
              end: Alignment(1, 1 - _controller.value),
              colors: isDark
                  ? [base, AppPalette.darkSurfaceAlt, AppPalette.darkBackground]
                  : [base, AppPalette.lightSurfaceAlt, const Color(0xFFEAF4EE)],
            ),
          ),
          child: widget.child,
        );
      },
    );
  }
}

class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
  });

  final Widget child;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        color: Theme.of(context).cardTheme.color,
        border: Border.all(
          color: isDark ? AppPalette.darkBorder : AppPalette.lightBorder,
        ),
      ),
      child: child,
    );
  }
}

class LeafLoader extends StatefulWidget {
  const LeafLoader({super.key, this.size = 52});

  final double size;

  @override
  State<LeafLoader> createState() => _LeafLoaderState();
}

class _LeafLoaderState extends State<LeafLoader>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        final scale = 0.82 + (_controller.value * 0.18);
        return Transform.scale(
          scale: scale,
          child: Icon(
            Icons.eco_rounded,
            size: widget.size,
            color: AppPalette.brandGreen,
          ),
        );
      },
    );
  }
}

class RotatingHexChain extends StatefulWidget {
  const RotatingHexChain({super.key, this.size = 86});

  final double size;

  @override
  State<RotatingHexChain> createState() => _RotatingHexChainState();
}

class _RotatingHexChainState extends State<RotatingHexChain>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: AnimatedBuilder(
        animation: _controller,
        builder: (context, _) {
          return Stack(
            alignment: Alignment.center,
            children: [
              Transform.rotate(
                angle: _controller.value * math.pi * 2,
                child: Icon(
                  Icons.hexagon_outlined,
                  size: widget.size,
                  color: AppPalette.accentBlue,
                ),
              ),
              const Icon(Icons.link_rounded, size: 30),
            ],
          );
        },
      ),
    );
  }
}
