class AcademicYears:

    """
    Activity choices
    """
    YEAR_2022_23 = '2022/23'
    YEAR_2023_24 = '2023/24'
    YEAR_2024_25 = '2024/25'
    YEAR_2025_26 = '2025/26'
    YEAR_2026_27 = '2026/27'
    YEAR_2027_28 = '2027/28'
    YEAR_2028_29 = '2028/29'
    YEAR_2029_30 = '2029/30'
    YEAR_2030_31 = '2030/31'
    YEAR_2031_32 = '2031/32'
    YEAR_2032_33 = '2032/33'

    __ALL__ = (YEAR_2022_23, YEAR_2023_24, YEAR_2024_25, YEAR_2025_26, YEAR_2026_27,
               YEAR_2027_28,YEAR_2028_29, YEAR_2029_30, YEAR_2030_31, YEAR_2031_32,
               YEAR_2032_33)
    __MODEL_CHOICES__ = (
        (academic_year, academic_year) for academic_year in __ALL__
    )
