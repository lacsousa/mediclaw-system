import { Badge, Box, Flex, Text } from "@chakra-ui/react";
import type { Message } from "@/types/api";
import { hasEducationalDisclaimer } from "@/lib/chat-disclaimer";
import { SourceAttribution } from "./SourceAttribution";
import { MessageContent } from "./MessageContent";

const FOOTER_DISCLAIMER = "ℹ Esta orientação é educativa e não substitui um profissional de saúde.";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "USER";
  const showFooterDisclaimer = !isUser && !hasEducationalDisclaimer(message.content);

  return (
    <Flex justify={isUser ? "flex-end" : "flex-start"} mb={4}>
      <Box maxW={{ base: "92%", md: "75%" }}>
        {!isUser && message.blocked_by_guardrail && (
          <Badge colorPalette="red" mb={1} borderRadius="md">
            Resposta limitada
          </Badge>
        )}
        <Box
          bg={isUser ? "teal.500" : "bg"}
          color={isUser ? "white" : "fg"}
          px={4}
          py={3}
          borderRadius="xl"
          borderWidth={isUser ? "0" : "1px"}
          borderColor="border"
          shadow={isUser ? "sm" : "card"}
          borderBottomRightRadius={isUser ? "sm" : "xl"}
          borderBottomLeftRadius={isUser ? "xl" : "sm"}
        >
          <MessageContent content={message.content} variant={isUser ? "user" : "assistant"} />
        </Box>
        {showFooterDisclaimer && (
          <Text fontSize="xs" color="fg.muted" mt={1.5}>
            {FOOTER_DISCLAIMER}
          </Text>
        )}
        {!isUser && <SourceAttribution citations={message.metadata?.citations} />}
      </Box>
    </Flex>
  );
}
