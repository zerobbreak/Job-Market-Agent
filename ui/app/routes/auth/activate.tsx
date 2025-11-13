import { Link } from "react-router"
import { Heading } from "~/components/ui/heading"
import { Text } from "~/components/ui/text"

export default function Activate() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-[#fcfbf8] py-12 px-4">
            <div className="w-full max-w-md text-center">
                <img src="/placeholder-logo.svg" alt="Job Market Agent Logo" className="h-12 mx-auto mb-6" />
                <Heading className="!text-black font-bold text-2xl mb-4">
                    Activate your account
                </Heading>
                <Text className="!text-black text-lg">
                    Check your email for the activation link.
                </Text>
                <div className="mt-8">
                    <Text className="!text-gray-600 text-sm">
                        Didn't receive the email? Check your spam folder or{" "}
                        <Link
                            to="/register"
                            className="!text-[#4b92ff] hover:!text-[#3a7ce8] font-medium"
                        >
                            try registering again
                        </Link>
                    </Text>
                </div>
            </div>
        </div>
    )
}
