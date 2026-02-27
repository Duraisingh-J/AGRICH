import 'dart:async';

import 'package:flutter/material.dart';

import '../core/i18n.dart';
import '../core/models.dart';
import '../features/auth/auth_flow.dart';
import '../features/shell/role_shell.dart';
import 'theme.dart';

class AgrichainApp extends StatefulWidget {
  const AgrichainApp({super.key});

  @override
  State<AgrichainApp> createState() => _AgrichainAppState();
}

class _AgrichainAppState extends State<AgrichainApp> {
  final I18nController _i18n = I18nController();
  ThemeMode _themeMode = ThemeMode.light;
  AuthSession? _session;
  bool _showSplash = true;

  @override
  void initState() {
    super.initState();
    Timer(const Duration(milliseconds: 2200), () {
      if (mounted) {
        setState(() => _showSplash = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _i18n,
      builder: (context, _) {
        return MaterialApp(
          title: 'AGRICHAIN',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.light(),
          darkTheme: AppTheme.dark(),
          themeMode: _themeMode,
          home: AnimatedSwitcher(
            duration: const Duration(milliseconds: 320),
            transitionBuilder: (child, animation) {
              final slide =
                  Tween<Offset>(
                    begin: const Offset(0.12, 0),
                    end: Offset.zero,
                  ).animate(
                    CurvedAnimation(
                      parent: animation,
                      curve: Curves.easeOutCubic,
                    ),
                  );
              return FadeTransition(
                opacity: animation,
                child: SlideTransition(position: slide, child: child),
              );
            },
            child: _showSplash
                ? SplashScreen(tagline: _i18n.t('tagline'))
                : _session == null
                ? AuthFlow(
                    i18n: _i18n,
                    onAuthenticated: (session) =>
                        setState(() => _session = session),
                  )
                : RoleShell(
                    session: _session!,
                    i18n: _i18n,
                    themeMode: _themeMode,
                    onThemeModeChanged: (mode) =>
                        setState(() => _themeMode = mode),
                    onLogout: () => setState(() => _session = null),
                  ),
          ),
        );
      },
    );
  }
}
