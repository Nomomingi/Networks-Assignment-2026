export const RootLayout = ({ children }: { children: React.ReactNode }) => {
    return (
        <html lang="en">
            <head>
                <title>Chat App</title>
            </head>
            <body>
                {children}
            </body>
        </html>
    )
}