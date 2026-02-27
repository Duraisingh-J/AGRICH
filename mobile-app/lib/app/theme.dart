import 'package:flutter/material.dart';

class AppPalette {
  static const brandGreen = Color(0xFF1E6B45);
  static const brandGreenDark = Color(0xFF13422E);
  static const accentGold = Color(0xFFD2A63E);
  static const premiumGold = accentGold;
  static const accentBlue = Color(0xFF2C7BE5);
  static const warningAmber = Color(0xFFF59E0B);

  static const lightBackground = Color(0xFFF2F4EF);
  static const lightSurface = Color(0xFFFFFFFF);
  static const lightSurfaceAlt = Color(0xFFE8ECE3);
  static const lightBorder = Color(0xFFC9D0C2);
  static const lightSelected = Color(0xFFE7DAB5);

  static const darkBackground = Color(0xFF0B1511);
  static const darkSurface = Color(0xFF12201A);
  static const darkSurfaceAlt = Color(0xFF1B2E25);
  static const darkBorder = Color(0xFF2E463A);
  static const darkSelected = Color(0xFF3A321C);
}

class AppTheme {
  static ThemeData light() {
    const scheme = ColorScheme(
      brightness: Brightness.light,
      primary: AppPalette.brandGreen,
      onPrimary: Colors.white,
      secondary: AppPalette.accentGold,
      onSecondary: Color(0xFF241A07),
      error: Color(0xFFBA1A1A),
      onError: Colors.white,
      surface: AppPalette.lightSurface,
      onSurface: Color(0xFF101828),
      tertiary: AppPalette.accentBlue,
      onTertiary: Colors.white,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: AppPalette.lightBackground,
      textTheme: _textTheme(const Color(0xFF101828)),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppPalette.lightSurface,
        foregroundColor: Color(0xFF101828),
        elevation: 0,
        toolbarHeight: 64,
      ),
      cardTheme: CardThemeData(
        color: AppPalette.lightSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppPalette.lightBorder),
        ),
      ),
      navigationBarTheme: const NavigationBarThemeData(
        backgroundColor: AppPalette.lightSurface,
        indicatorColor: Color(0xFFE7DAB5),
        surfaceTintColor: Colors.transparent,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: ButtonStyle(
          minimumSize: const WidgetStatePropertyAll(Size.fromHeight(50)),
          backgroundColor: const WidgetStatePropertyAll(AppPalette.brandGreen),
          foregroundColor: const WidgetStatePropertyAll(Colors.white),
          shape: WidgetStatePropertyAll(
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: ButtonStyle(
          minimumSize: const WidgetStatePropertyAll(Size.fromHeight(50)),
          side: const WidgetStatePropertyAll(
            BorderSide(color: AppPalette.lightBorder),
          ),
          shape: WidgetStatePropertyAll(
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppPalette.lightSurfaceAlt,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 12,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppPalette.lightBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppPalette.lightBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(
            color: AppPalette.brandGreen,
            width: 1.5,
          ),
        ),
      ),
    );
  }

  static ThemeData dark() {
    const scheme = ColorScheme(
      brightness: Brightness.dark,
      primary: AppPalette.brandGreen,
      onPrimary: Colors.white,
      secondary: AppPalette.accentGold,
      onSecondary: Color(0xFF221905),
      error: Color(0xFFFFB4AB),
      onError: Color(0xFF690005),
      surface: AppPalette.darkSurface,
      onSurface: Color(0xFFF2F6F3),
      tertiary: AppPalette.accentBlue,
      onTertiary: Colors.white,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: AppPalette.darkBackground,
      textTheme: _textTheme(const Color(0xFFF2F6F3)),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppPalette.darkSurface,
        foregroundColor: Color(0xFFF2F6F3),
        elevation: 0,
        toolbarHeight: 64,
      ),
      cardTheme: CardThemeData(
        color: AppPalette.darkSurface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppPalette.darkBorder),
        ),
      ),
      navigationBarTheme: const NavigationBarThemeData(
        backgroundColor: AppPalette.darkSurface,
        indicatorColor: AppPalette.darkSelected,
        surfaceTintColor: Colors.transparent,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: ButtonStyle(
          minimumSize: const WidgetStatePropertyAll(Size.fromHeight(50)),
          backgroundColor: const WidgetStatePropertyAll(AppPalette.accentGold),
          foregroundColor: const WidgetStatePropertyAll(Color(0xFF231A07)),
          shape: WidgetStatePropertyAll(
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: ButtonStyle(
          minimumSize: const WidgetStatePropertyAll(Size.fromHeight(50)),
          side: const WidgetStatePropertyAll(
            BorderSide(color: AppPalette.darkBorder),
          ),
          foregroundColor: const WidgetStatePropertyAll(Color(0xFFE2ECE7)),
          shape: WidgetStatePropertyAll(
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppPalette.darkSurfaceAlt,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 12,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppPalette.darkBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppPalette.darkBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(
            color: AppPalette.accentGold,
            width: 1.5,
          ),
        ),
      ),
    );
  }

  static TextTheme _textTheme(Color bodyColor) {
    return TextTheme(
      headlineLarge: TextStyle(
        fontFamily: 'Poppins',
        fontWeight: FontWeight.w700,
        fontSize: 32,
        height: 1.2,
        color: bodyColor,
      ),
      headlineMedium: TextStyle(
        fontFamily: 'Poppins',
        fontWeight: FontWeight.w700,
        fontSize: 28,
        height: 1.2,
        color: bodyColor,
      ),
      titleLarge: TextStyle(
        fontFamily: 'Poppins',
        fontWeight: FontWeight.w700,
        fontSize: 21,
        height: 1.25,
        color: bodyColor,
      ),
      titleMedium: TextStyle(
        fontFamily: 'Inter',
        fontWeight: FontWeight.w600,
        fontSize: 16,
        height: 1.3,
        color: bodyColor,
      ),
      bodyLarge: TextStyle(
        fontFamily: 'Inter',
        fontWeight: FontWeight.w500,
        fontSize: 15,
        height: 1.35,
        color: bodyColor,
      ),
      bodyMedium: TextStyle(
        fontFamily: 'Inter',
        fontWeight: FontWeight.w500,
        fontSize: 14,
        height: 1.35,
        color: bodyColor,
      ),
      labelLarge: TextStyle(
        fontFamily: 'Inter',
        fontWeight: FontWeight.w700,
        fontSize: 14,
        height: 1.2,
        color: bodyColor,
      ),
    );
  }
}
