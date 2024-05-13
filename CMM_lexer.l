%{
#include <stdio.h>
#include <string.h>

int isType(char *str) {
    if (strcmp(str, "int") == 0 ||
        strcmp(str, "double") == 0 ||
        strcmp(str, "float") == 0 ||
        strcmp(str, "char") == 0 ||
        strcmp(str, "string") == 0 ||
        strcmp(str, "void") == 0)
        return 1;
    return 0;
}

%}

/* Static Definitions */

VARSTRING [a-zA-Z_][a-zA-Z0-9_]*
DECIMAL [0-9]+\.[0-9]+
STRING .+

%%

"if"                    { printf("IF\n"); }
"else"                  { printf("ELSE\n"); }
"while"                 { printf("WHILE\n"); }
"return"                { printf("RETURN\n"); }
"read"                  { printf("READ\n"); }
"write"                 { printf("WRITE\n"); }
"writeln"               { printf("WRITELN\n"); }
"break"                 { printf("BREAK\n"); }
"("                     { printf("LPAREN\n"); }
")"                     { printf("RPAREN\n"); }
"{"                     { printf("LBRACE\n"); }
"}"                     { printf("RBRACE\n"); }
";"                     { printf("SEMICOLON\n"); }
","                     { printf("COMMA\n"); }
"["                     { printf("LBRACKET\n"); }
"]"                     { printf("RBRACKET\n"); }
"=="                    { printf("EQ\n"); }
"!="                    { printf("NEQ\n"); }
"<="                    { printf("LEQ\n"); }
">="                    { printf("GEQ\n"); }
"="                     { printf("ASSIGN\n"); }
"<"                     { printf("LT\n"); }
">"                     { printf("GT\n"); }
"+"                     { printf("PLUS\n"); }
"-"                     { printf("MINUS\n"); }
"*"                     { printf("TIMES\n"); }
"/"                     { printf("DIVIDE\n"); }
"&&"                    { printf("AND\n"); }
"||"                    { printf("OR\n"); }
"!"                     { printf("NOT\n"); }

{DECIMAL}               { printf("DECIMAL(%s)\n", yytext); }
"float"                 { printf("FLOAT\n"); }
"'"                     { printf("SINGLEQUOTE\n"); }
"\""                    { printf("DOUBLEQUOTE\n"); }
"for"                   { printf("FOR\n"); }
[0-9]+                  { printf("NUM(%s)\n", yytext); }

{VARSTRING}"("          { printf("FUNCNAME(%s)\nLPAREN\n", yytext); }

"\""{STRING}"\""        { printf("STRING(%s)\n", yytext); }

{VARSTRING}             {
                            if (isType(yytext)) {
                                printf("TYPE(%s)\n", yytext);
                            } else {
                                printf("ID(%s)\n", yytext);
                            }
                        }

[ \t\n]                 // Skip whitespace and newline

.                       { fprintf(stderr, "Unknown token: %s\n", yytext); }

%%

int yywrap() {}

int main() {
    yylex();
    return 0;
}
